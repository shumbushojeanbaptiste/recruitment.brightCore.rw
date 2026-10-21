
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.repositories import application_repository, job_repository
from app.services.cv_storage import delete_cv, store_cv
from app.services.job_service import utc_now


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
    application_id: uuid.UUID,
    new_status: str,
    note: str | None,
) -> Application:
    application = application_repository.get_by_id(
        db, application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if application.status in ("accepted", "rejected"):
        if application.status != new_status:
            raise HTTPException(
                status_code=409,
                detail="A final application decision cannot be changed",
            )

    application.status = new_status
    application.status_note = note

    return application_repository.save(db, application)
