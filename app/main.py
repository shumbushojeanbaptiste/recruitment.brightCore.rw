from contextlib import asynccontextmanager
import logging
import time
import uuid

import redis.asyncio as redis

from fastapi import FastAPI, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import get_settings
from app.db.session import engine
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

settings = get_settings()
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.redis = redis_client
    yield
    engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="BrightCore recruitment platform API",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logging.getLogger("brightcore.http").exception(
            "request_failed request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    logging.getLogger("brightcore.http").info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )

    return response


app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
        "docs": "/docs",
    }




@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "dependency": "postgres",
            },
        ) from exc

    try:
        if not await redis_client.ping():
            raise RuntimeError("Redis ping failed")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "dependency": "redis",
            },
        ) from exc

    return {
        "status": "ready",
        "postgres": "ok",
        "redis": "ok",
    }