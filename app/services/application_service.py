
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.repositories import application_repository, job_repository
from app.services.cv_storage import delete_cv, store_cv
from app.services.job_service import utc_now

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.application_status_history import ApplicationStatusHistory
from app.models.audit_event import AuditEvent
from app.services.notification_service import (
    log_application_status_notification,
)



async def submit_application(
    db: Session,
    *,
    job_id: uuid.UUID,
    full_name: str,
    email: str,
    phone: str,
    cover_note: str | None,
    cv: UploadFile,
) -> Application:
    job = job_repository.get_public_job(
        db,
        job_id,
        now=utc_now(),
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or no longer accepting applications",
        )

    normalized_email = email.strip().lower()

    # Check early for a friendly response. The database unique constraint
    # remains the authoritative protection against concurrent requests.
    from sqlalchemy import select

    existing = db.scalar(
        select(Application).where(
            Application.job_id == job_id,
            Application.email == normalized_email,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This email has already applied for this job",
        )

    stored = await store_cv(cv)

    application = Application(
        job_id=job_id,
        full_name=" ".join(full_name.split()),
        email=normalized_email,
        phone=phone.strip(),
        cover_note=cover_note.strip() if cover_note else None,
        cv_storage_key=stored.storage_key,
        cv_original_filename=stored.original_filename,
        cv_size_bytes=stored.size_bytes,
        cv_sha256=stored.sha256,
        status="submitted",
    )

    try:
        return application_repository.create(db, application)
    except IntegrityError as exc:
        db.rollback()
        delete_cv(stored.storage_key)
        raise HTTPException(
            status_code=409,
            detail="This email has already applied for this job",
        ) from exc
    except Exception:
        db.rollback()
        delete_cv(stored.storage_key)
        raise



def update_application_status(
    db: Session,
    application_id,
    new_status: str,
    note: str | None,
    actor_id,
) -> Application:
    application = application_repository.get_by_id(
        db, application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    previous_status = application.status

    # Repeating the same status is harmless and creates no duplicate history.
    if previous_status == new_status:
        return application

    # Accepted and rejected are final decisions in this workflow.
    if previous_status in ("accepted", "rejected"):
        raise HTTPException(
            status_code=409,
            detail="A final application decision cannot be changed",
        )

    try:
        application.status = new_status
        application.status_note = note

        db.add(
            ApplicationStatusHistory(
                application_id=application.id,
                previous_status=previous_status,
                new_status=new_status,
                note=note,
                changed_by=actor_id,
            )
        )

        db.add(
            AuditEvent(
                actor_id=actor_id,
                action="APPLICATION_STATUS_CHANGED",
                resource_type="application",
                resource_id=str(application.id),
                details={
                    "previous_status": previous_status,
                    "new_status": new_status,
                },
            )
        )

        # All database changes are committed together.
        db.commit()
        db.refresh(application)

    except Exception:
        db.rollback()
        raise

    # Notification logging is deliberately outside the database transaction.
    # Failure to log a notification must not undo a valid status change.
    try:
        log_application_status_notification(
            application_id=application.id,
            recipient_email=application.email,
            status=application.status,
            note=application.status_note,
        )
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Failed to log application status notification"
        )

    return application