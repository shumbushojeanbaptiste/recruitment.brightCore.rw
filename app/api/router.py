from fastapi import APIRouter

from app.api.routes import (
    admin_applications,
    admin_audit,
    admin_dashboard,
    admin_jobs,
    applications,
    auth,
    jobs,
    candidate,
)


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(admin_jobs.router)
api_router.include_router(applications.router)
api_router.include_router(admin_applications.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_audit.router)
api_router.include_router(candidate.router)