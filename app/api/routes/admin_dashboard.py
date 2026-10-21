from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["admin-dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
)
def dashboard_summary(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return get_dashboard_summary(db)