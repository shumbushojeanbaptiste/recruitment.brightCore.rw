
from fastapi import APIRouter

from app.api.routes.admin_applications import (
    router as admin_applications_router,
)
from app.api.routes.admin_jobs import router as admin_jobs_router
from app.api.routes.applications import router as applications_router
from app.api.routes.auth import router as auth_router
from app.api.routes.jobs import router as jobs_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(jobs_router)
api_router.include_router(admin_jobs_router)
api_router.include_router(applications_router)
api_router.include_router(admin_applications_router)
