from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def create(db: Session, event: AuditEvent) -> AuditEvent:
    db.add(event)
    return event


def list_events(
    db: Session,
    *,
    page: int,
    page_size: int,
    action: str | None = None,
):
    query = select(AuditEvent)

    if action:
        query = query.where(AuditEvent.action == action)

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    items = db.scalars(
        query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return items, total