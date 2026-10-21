
import math
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.application_repository import (
    get_by_id,
    list_applications,
)
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationPublic,
    ApplicationStatusUpdate,
)
from app.services.application_service import update_application_status
from app.services.cv_storage import resolve_cv_path

router = APIRouter(
    prefix="/admin/applications",
    tags=["admin applications"],
)


@router.get("", response_model=ApplicationListResponse)
def list_admin_applications(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    job_id: uuid.UUID | None = None,
    status_filter: Annotated[
        Literal["submitted", "under_review", "accepted", "rejected"] | None,
        Query(alias="status"),
    ] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> ApplicationListResponse:
    items, total = list_applications(
        db,
        page=page,
        page_size=page_size,
        job_id=job_id,
        application_status=status_filter,
        search=q,
    )

    return ApplicationListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{application_id}", response_model=ApplicationPublic)
def get_admin_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ApplicationPublic:
    application = get_by_id(db, application_id)

    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    return application


# @router.patch(
#     "/{application_id}/status",
#     response_model=ApplicationPublic,
# )
# def change_application_status(
#     application_id: uuid.UUID,
#     payload: ApplicationStatusUpdate,
#     db: Session = Depends(get_db),
#     _: User = Depends(require_admin),
# ) -> ApplicationPublic:
#     return update_application_status(
#         db,
#         application_id,
#         payload.status,
#         payload.note,
#     )

@router.patch("/{application_id}/status", response_model=ApplicationPublic)
def change_application_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return update_application_status(
        db=db,
        application_id=application_id,
        new_status=payload.status,
        note=payload.note,
        actor_id=admin.id,
    )


@router.get("/{application_id}/cv")
def download_application_cv(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> FileResponse:
    application = get_by_id(db, application_id)

    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    try:
        path = resolve_cv_path(application.cv_storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="CV file not found",
        ) from exc

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=application.cv_original_filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )
