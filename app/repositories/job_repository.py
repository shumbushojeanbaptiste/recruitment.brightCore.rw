
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.job import Job


def get_by_id(db: Session, job_id: uuid.UUID) -> Job | None:
    return db.get(Job, job_id)


def create(db: Session, job: Job) -> Job:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def save(db: Session, job: Job) -> Job:
    db.commit()
    db.refresh(job)
    return job


def list_admin_jobs(db: Session) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc())
    return list(db.scalars(statement).all())


def list_public_jobs(
    db: Session,
    *,
    now: datetime,
    page: int,
    page_size: int,
    search: str | None,
    location: str | None,
    employment_type: str | None,
) -> tuple[list[Job], int]:
    filters = [
        Job.status == "published",
        or_(Job.expires_at.is_(None), Job.expires_at > now),
    ]

    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term),
                Job.department.ilike(term),
            )
        )

    if location:
        filters.append(Job.location.ilike(f"%{location.strip()}%"))

    if employment_type:
        filters.append(Job.employment_type == employment_type)

    count_statement = (
        select(func.count()).select_from(Job).where(*filters)
    )
    total = db.scalar(count_statement) or 0

    statement = (
        select(Job)
        .where(*filters)
        .order_by(Job.published_at.desc(), Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    items = list(db.scalars(statement).all())
    return items, total


def get_public_job(
    db: Session,
    job_id: uuid.UUID,
    *,
    now: datetime,
) -> Job | None:
    statement = select(Job).where(
        Job.id == job_id,
        Job.status == "published",
        or_(Job.expires_at.is_(None), Job.expires_at > now),
    )
    return db.scalar(statement)
