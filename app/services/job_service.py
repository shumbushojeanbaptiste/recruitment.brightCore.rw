
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.user import User
from app.repositories import job_repository
from app.schemas.job import JobCreate, JobUpdate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)



def create_job(
    db: Session,
    payload: JobCreate,
    current_user: User,
) -> Job:
    if payload.expires_at is not None and payload.expires_at <= utc_now():
        raise HTTPException(
            status_code=422,
            detail="expires_at must be in the future",
        )

    job = Job(
        **payload.model_dump(),
        status="draft",
        created_by=current_user.id,
    )
    return job_repository.create(db, job)

def update_job(
    db: Session,
    job_id: uuid.UUID,
    payload: JobUpdate,
) -> Job:
    job = job_repository.get_by_id(db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "closed":
        raise HTTPException(
            status_code=409,
            detail="Closed jobs cannot be edited",
        )

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(job, field, value)

    if (
        job.salary_min is not None
        and job.salary_max is not None
        and job.salary_max < job.salary_min
    ):
        raise HTTPException(
            status_code=422,
            detail="salary_max must be greater than or equal to salary_min",
        )

    if job.expires_at is not None:
        if job.expires_at.utcoffset() is None:
            raise HTTPException(
                status_code=422,
                detail="expires_at must include a timezone",
            )
        if job.expires_at <= utc_now():
            raise HTTPException(
                status_code=422,
                detail="expires_at must be in the future",
            )

    return job_repository.save(db, job)


def publish_job(db: Session, job_id: uuid.UUID) -> Job:
    job = job_repository.get_by_id(db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "closed":
        raise HTTPException(
            status_code=409,
            detail="A closed job cannot be published again",
        )

    if job.expires_at is not None and job.expires_at <= utc_now():
        raise HTTPException(
            status_code=422,
            detail="An expired job cannot be published",
        )

    job.status = "published"

    if job.published_at is None:
        job.published_at = utc_now()

    return job_repository.save(db, job)


def close_job(db: Session, job_id: uuid.UUID) -> Job:
    job = job_repository.get_by_id(db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "closed"
    return job_repository.save(db, job)


def get_public_job_or_404(
    db: Session,
    job_id: uuid.UUID,
) -> Job:
    job = job_repository.get_public_job(
        db,
        job_id,
        now=utc_now(),
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job
