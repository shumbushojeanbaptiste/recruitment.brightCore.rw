
import math
import uuid
from datetime import timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import job_repository
from app.schemas.job import JobListResponse, JobPublic, EmploymentType
from app.services.job_service import get_public_job_or_404, utc_now

router = APIRouter(prefix="/jobs", tags=["public jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    q: Annotated[str | None, Query(max_length=100)] = None,
    location: Annotated[str | None, Query(max_length=160)] = None,
    employment_type: EmploymentType | None = None,
) -> JobListResponse:
    now = utc_now()
    items, total = job_repository.list_public_jobs(
        db,
        now=now,
        page=page,
        page_size=page_size,
        search=q,
        location=location,
        employment_type=employment_type,
    )

    return JobListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{job_id}", response_model=JobPublic)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return get_public_job_or_404(db, job_id)
