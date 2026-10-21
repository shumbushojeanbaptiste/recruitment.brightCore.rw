from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_status_history import ApplicationStatusHistory


def list_for_application(db: Session, application_id):
    return db.scalars(
        select(ApplicationStatusHistory)
        .where(
            ApplicationStatusHistory.application_id == application_id
        )
        .order_by(
            ApplicationStatusHistory.changed_at.asc(),
            ApplicationStatusHistory.id.asc(),
        )
    ).all()