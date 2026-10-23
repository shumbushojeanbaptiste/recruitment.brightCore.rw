
def test_login_is_rate_limited(client):
    payload = {
        "email": "missing-user@example.com",
        "password": "IncorrectPassword-123!",
    }

    responses = [
        client.post("/api/v1/auth/login", json=payload)
        for _ in range(11)
    ]

    # The first ten requests reach the existing login logic.
    assert all(
        response.status_code != 429
        for response in responses[:10]
    )

    # The eleventh request exceeds the configured ten-per-minute limit.
    assert responses[10].status_code == 429
    assert responses[10].headers.get("Retry-After") is not None


def test_application_submission_is_rate_limited(client):
    url = "/api/v1/jobs/00000000-0000-0000-0000-000000000001/applications"
    responses = [client.post(url) for _ in range(11)]

    assert all(
        response.status_code != 429
        for response in responses[:10]
    )
    assert responses[10].status_code == 429
    assert responses[10].headers.get("Retry-After") is not None
