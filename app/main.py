from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import logging
import time
import uuid

import redis.asyncio as redis

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_204_NO_CONTENT
from typing import Any

from app.core.metrics import (
    HTTP_REQUESTS,
    HTTP_REQUEST_DURATION,
    metrics_response,
)
from app.core.config import get_settings
from app.db.session import engine
from app.api.router import api_router


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "event",
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "exception_type",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


logging.basicConfig(
    level=logging.INFO,
)
for handler in logging.getLogger().handlers:
    handler.setFormatter(JsonLogFormatter())

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


def _is_api_path(path: str) -> bool:
    return path == settings.api_v1_prefix or path.startswith(
        f"{settings.api_v1_prefix}/"
    )


def _response_meta(request: Request) -> dict[str, str]:
    return {"request_id": request.state.request_id}


def _error_response(
    request: Request,
    *,
    code: str,
    message: str,
    details: object = None,
    status_code: int,
    response_headers: dict[str, str] | None = None,
) -> JSONResponse:
    headers = dict(response_headers or {})
    headers["X-Request-ID"] = request.state.request_id
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content=jsonable_encoder(
            {
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                },
                "meta": _response_meta(request),
            },
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def api_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> Response:
    if not _is_api_path(request.url.path):
        return await http_exception_handler(request, exc)

    detail = exc.detail
    message = (
        detail
        if isinstance(detail, str)
        else "The request could not be completed."
    )
    code = {
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
    }.get(exc.status_code, "http_error")
    details = None if isinstance(detail, str) else detail
    return _error_response(
        request,
        code=code,
        message=message,
        details=details,
        status_code=exc.status_code,
        response_headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def api_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    if not _is_api_path(request.url.path):
        return await http_exception_handler(
            request,
            HTTPException(status_code=422, detail=exc.errors()),
        )

    details = [
        {
            "location": error.get("loc", []),
            "message": error.get("msg", "Invalid value."),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return _error_response(
        request,
        code="validation_error",
        message="Request validation failed.",
        details=details,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.exception_handler(Exception)
async def api_unhandled_exception_handler(
    request: Request,
    _exc: Exception,
) -> Response:
    if not _is_api_path(request.url.path):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error."},
        )
    route_info = request.scope.get("route")
    route = getattr(route_info, "path", "unmatched")
    logging.getLogger("brightcore.http").warning(
        "internal_error_response",
        extra={
            "event": "internal_error_response",
            "request_id": request.state.request_id,
            "method": request.method,
            "path": route,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "exception_type": type(_exc).__name__,
        },
    )
    return _error_response(
        request,
        code="internal_server_error",
        message="An unexpected server error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()

    if request.url.path == "/metrics":
        return await call_next(request)

    route = "unmatched"
    try:
        response = await call_next(request)
    except Exception:
        route_info = request.scope.get("route")
        if route_info is not None:
            route = getattr(route_info, "path", route)
        elapsed = time.perf_counter() - started
        HTTP_REQUESTS.labels(
            request.method,
            route,
            str(status.HTTP_500_INTERNAL_SERVER_ERROR),
        ).inc()
        HTTP_REQUEST_DURATION.labels(request.method, route).observe(elapsed)
        logging.getLogger("brightcore.http").exception(
            "request_failed",
            extra={
                "event": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": route,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "duration_ms": round(elapsed * 1000, 2),
            },
        )
        raise

    route_info = request.scope.get("route")
    if route_info is not None:
        route = getattr(route_info, "path", route)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    HTTP_REQUESTS.labels(
        request.method,
        route,
        str(response.status_code),
    ).inc()
    HTTP_REQUEST_DURATION.labels(request.method, route).observe(elapsed_ms / 1000)
    response.headers["X-Request-ID"] = request_id

    logging.getLogger("brightcore.http").info(
        "request_complete",
        extra={
            "event": "request_complete",
            "request_id": request_id,
            "method": request.method,
            "path": route,
            "status_code": response.status_code,
            "duration_ms": elapsed_ms,
        },
    )

    if (
        _is_api_path(request.url.path)
        and 200 <= response.status_code < 300
        and response.status_code != HTTP_204_NO_CONTENT
        and response.headers.get("content-type", "").startswith("application/json")
    ):
        body = b"".join([chunk async for chunk in response.body_iterator])
        data = json.loads(body) if body else None
        headers = {
            name: value
            for name, value in response.headers.items()
            if name.lower()
            not in {"content-length", "content-type", "x-request-id"}
        }
        headers["X-Request-ID"] = request_id
        return JSONResponse(
            status_code=response.status_code,
            headers=headers,
            background=response.background,
            content={
                "success": True,
                "data": data,
                "meta": _response_meta(request),
            },
        )

    return response


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics() -> Response:
    return metrics_response()


app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    meta_schema = {
        "type": "object",
        "required": ["request_id"],
        "properties": {"request_id": {"type": "string"}},
    }
    schema["components"]["schemas"]["ApiErrorResponse"] = {
        "type": "object",
        "required": ["success", "error", "meta"],
        "properties": {
            "success": {"type": "boolean", "enum": [False]},
            "error": {
                "type": "object",
                "required": ["code", "message", "details"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {},
                },
            },
            "meta": meta_schema,
        },
    }

    for path, methods in schema["paths"].items():
        if not _is_api_path(path):
            continue
        for operation in methods.values():
            for response_code, response_schema in operation.get(
                "responses", {}
            ).items():
                try:
                    code = int(response_code)
                except ValueError:
                    continue
                json_content = response_schema.get("content", {}).get(
                    "application/json"
                )
                if json_content is None:
                    continue
                if 200 <= code < 300 and code != HTTP_204_NO_CONTENT:
                    data_schema = json_content.get("schema", {})
                    json_content["schema"] = {
                        "type": "object",
                        "required": ["success", "data", "meta"],
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "enum": [True],
                            },
                            "data": data_schema,
                            "meta": meta_schema,
                        },
                    }
                elif code >= 400:
                    json_content["schema"] = {
                        "$ref": "#/components/schemas/ApiErrorResponse"
                    }

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


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