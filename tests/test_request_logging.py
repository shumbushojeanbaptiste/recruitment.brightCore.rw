import json
import logging
import uuid

from app.main import JsonLogFormatter


def test_request_has_id_header_and_is_logged(client, caplog):
    caplog.set_level(logging.INFO, logger="brightcore.http")
    response = client.get("/")

    request_id = response.headers["X-Request-ID"]
    uuid.UUID(request_id)

    request_record = next(
        record
        for record in caplog.records
        if record.name == "brightcore.http"
        and record.event == "request_complete"
    )
    log_payload = json.loads(JsonLogFormatter().format(request_record))

    assert log_payload["request_id"] == request_id
    assert log_payload["method"] == "GET"
    assert log_payload["path"] == "/"
    assert log_payload["status_code"] == 200
    assert isinstance(log_payload["duration_ms"], float)

    assert any(
        record.name == "brightcore.http"
        and "request_complete" in record.message
        and record.request_id == request_id
        and record.event == "request_complete"
        for record in caplog.records
    )
