
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application


def create(db: Session, application: Application) -> Application:
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_by_id(
    db: Session,
    application_id: uuid.UUID,
) -> Application | None:
    return db.get(Application, application_id)


def list_applications(
    db: Session,
    *,
    page: int,
    page_size: int,
    job_id: uuid.UUID | None,
    application_status: str | None,
    search: str | None,
) -> tuple[list[Application], int]:
    statement = select(Application)
    count_statement = select(func.count()).select_from(Application)

    if job_id is not None:
        statement = statement.where(Application.job_id == job_id)
        count_statement = count_statement.where(
            Application.job_id == job_id
        )

    if application_status is not None:
        statement = statement.where(
            Application.status == application_status
        )
        count_statement = count_statement.where(
            Application.status == application_status
        )

    if search:
        term = f"%{search.strip()}%"
        filters = (
            Application.full_name.ilike(term)
            | Application.email.ilike(term)
        )
        statement = statement.where(filters)
        count_statement = count_statement.where(filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement
        .order_by(Application.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return list(db.scalars(statement).all()), total


def save(db: Session, application: Application) -> Application:
    db.commit()
    db.refresh(application)
    return application
