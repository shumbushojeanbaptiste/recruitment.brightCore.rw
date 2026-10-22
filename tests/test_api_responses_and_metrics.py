def test_api_success_uses_standard_envelope_and_request_id(client):
    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.json() == {
        "success": True,
        "data": {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "pages": 0,
        },
        "meta": {"request_id": response.headers["X-Request-ID"]},
    }


def test_metrics_endpoint_exposes_prometheus_format(client):
    client.get("/api/v1/jobs")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "brightcore_http_requests_total" in response.text
    assert "brightcore_http_request_duration_seconds" in response.text


def test_api_validation_error_uses_standard_error_envelope(client):
    response = client.post("/api/v1/auth/login", json={})

    assert response.status_code == 422
    envelope = response.json()
    assert envelope["success"] is False
    assert envelope["error"]["code"] == "validation_error"
    assert envelope["error"]["details"]
    assert envelope["meta"]["request_id"] == response.headers["X-Request-ID"]


def test_openapi_documents_api_response_envelopes(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    success_schema = schema["paths"]["/api/v1/jobs"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert set(success_schema["required"]) == {"success", "data", "meta"}

    error_schema = schema["paths"]["/api/v1/jobs"]["get"]["responses"]["422"][
        "content"
    ]["application/json"]["schema"]
    assert error_schema["$ref"] == "#/components/schemas/ApiErrorResponse"
