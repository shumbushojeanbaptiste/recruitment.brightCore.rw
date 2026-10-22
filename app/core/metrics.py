import os

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector
from starlette.responses import Response


HTTP_REQUESTS = Counter(
    "brightcore_http_requests_total",
    "Total HTTP requests handled by the API.",
    ("method", "route", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "brightcore_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "route"),
)


def metrics_response() -> Response:
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        content = generate_latest(registry)
    else:
        content = generate_latest()

    return Response(content=content, media_type=CONTENT_TYPE_LATEST)
