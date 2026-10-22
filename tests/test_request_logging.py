import logging
import uuid


def test_request_has_id_header_and_is_logged(client, caplog):
    caplog.set_level(logging.INFO, logger="brightcore.http")
    response = client.get("/")

    request_id = response.headers["X-Request-ID"]
    uuid.UUID(request_id)

    assert any(
        record.name == "brightcore.http"
        and "request_complete" in record.message
        and request_id in record.message
        for record in caplog.records
    )
