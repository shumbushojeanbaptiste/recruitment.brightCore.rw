
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.application_status_history import ApplicationStatusHistory
from app.models.audit_event import AuditEvent
from app.services.application_service import update_application_status

from tests.helpers import (
    create_application,
    create_published_job,
    create_user,
)


def test_status_change_creates_history_and_audit(db_session):
    admin = create_user(db_session)
    job = create_published_job(db_session, admin.id)
    application = create_application(db_session, job.id)

    updated = update_application_status(
        db=db_session,
        application_id=application.id,
        new_status="under_review",
        note="Initial screening started",
        actor_id=admin.id,
    )

    assert updated.status == "under_review"
    assert updated.status_note == "Initial screening started"

    history = db_session.scalars(
        select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application.id
        )
    ).all()

    assert len(history) == 1
    assert history[0].previous_status == "submitted"
    assert history[0].new_status == "under_review"
    assert history[0].changed_by == admin.id

    audit = db_session.scalars(
        select(AuditEvent).where(
            AuditEvent.resource_id == str(application.id)
        )
    ).all()

    assert len(audit) == 1
    assert audit[0].action == "APPLICATION_STATUS_CHANGED"
    assert audit[0].actor_id == admin.id


def test_final_decision_cannot_be_reversed(db_session):
    admin = create_user(db_session)
    job = create_published_job(db_session, admin.id)
    application = create_application(db_session, job.id)

    update_application_status(
        db=db_session,
        application_id=application.id,
        new_status="accepted",
        note="Successful interview",
        actor_id=admin.id,
    )

    with pytest.raises(HTTPException) as error:
        update_application_status(
            db=db_session,
            application_id=application.id,
            new_status="rejected",
            note="Attempt to reverse the decision",
            actor_id=admin.id,
        )

    assert error.value.status_code == 409

    db_session.refresh(application)
    assert application.status == "accepted"


def test_repeating_same_status_does_not_create_duplicate_history(
    db_session,
):
    admin = create_user(db_session)
    job = create_published_job(db_session, admin.id)
    application = create_application(db_session, job.id)

    update_application_status(
        db=db_session,
        application_id=application.id,
        new_status="under_review",
        note="Screening started",
        actor_id=admin.id,
    )

    update_application_status(
        db=db_session,
        application_id=application.id,
        new_status="under_review",
        note="Duplicate transition",
        actor_id=admin.id,
    )

    history = db_session.scalars(
        select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application.id
        )
    ).all()

    assert len(history) == 1
