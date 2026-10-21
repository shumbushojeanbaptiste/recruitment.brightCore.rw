import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repository import list_events
from app.repositories.application_history_repository import (
    list_for_application,
)
from app.schemas.audit import (
    ApplicationStatusHistoryPublic,
    AuditEventListResponse,
    AuditEventPublic,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin-audit"],
)


@router.get(
    "/applications/{application_id}/history",
    response_model=list[ApplicationStatusHistoryPublic],
)
def application_history(
    application_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    import uuid
    from fastapi import HTTPException

    try:
        parsed_id = uuid.UUID(application_id)
    except ValueError:
        raise HTTPException(422, detail="Invalid application ID")

    from app.repositories.application_repository import get_by_id

    if get_by_id(db, parsed_id) is None:
        raise HTTPException(404, detail="Application not found")

    return list_for_application(db, parsed_id)


@router.get(
    "/audit-events",
    response_model=AuditEventListResponse,
)
def audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    items, total = list_events(
        db,
        page=page,
        page_size=page_size,
        action=action,
    )

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": math.ceil(total / page_size) if total else 0,
    }