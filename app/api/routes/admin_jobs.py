
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories import job_repository
from app.schemas.job import JobAdmin, JobCreate, JobUpdate
from app.services import job_service

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin jobs"],
)


@router.post(
    "",
    response_model=JobAdmin,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return job_service.create_job(db, payload, current_user)


@router.get("", response_model=list[JobAdmin])
def list_jobs_admin(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return job_repository.list_admin_jobs(db)


@router.get("/{job_id}", response_model=JobAdmin)
def get_job_admin(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    job = job_repository.get_by_id(db, job_id)

    if job is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.patch("/{job_id}", response_model=JobAdmin)
def update_job(
    job_id: uuid.UUID,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return job_service.update_job(db, job_id, payload)


@router.post("/{job_id}/publish", response_model=JobAdmin)
def publish_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return job_service.publish_job(db, job_id)


@router.post("/{job_id}/close", response_model=JobAdmin)
def close_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return job_service.close_job(db, job_id)
