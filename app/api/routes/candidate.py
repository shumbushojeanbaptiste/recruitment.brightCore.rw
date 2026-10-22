
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.candidate import (
    CandidateApplicationItem,
    CandidateApplicationListResponse,
)

router = APIRouter(
    prefix="/candidate",
    tags=["Candidate Portal"],
)


@router.get(
    "/applications",
    response_model=CandidateApplicationListResponse,
)
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CandidateApplicationListResponse:
    email = current_user.email.strip().lower()

    filters = [func.lower(Application.email) == email]

    total = db.scalar(
        select(func.count(Application.id)).where(*filters)
    ) or 0

    statement = (
        select(Application, Job.title)
        .join(Job, Application.job_id == Job.id)
        .where(*filters)
        .order_by(Application.created_at.desc())
    )
    rows = db.execute(statement).all()

    return CandidateApplicationListResponse(
        items=[
            CandidateApplicationItem(
                id=application.id,
                job_id=application.job_id,
                job_title=job_title,
                full_name=application.full_name,
                email=application.email,
                status=application.status,
                status_note=application.status_note,
                created_at=application.created_at,
                updated_at=application.updated_at,
            )
            for application, job_title in rows
        ],
        total=total,
    )


@router.get("/profile")
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at,
    }
