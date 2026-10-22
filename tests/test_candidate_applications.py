from app.api.deps import get_current_user
from app.main import app
from app.models.user import User

from tests.helpers import create_application, create_published_job


def test_candidate_applications_include_job_title(client, db_session):
    candidate = User(
        full_name="Test Candidate",
        email="candidate@example.com",
        password_hash="test-password-hash",
        role="candidate",
        is_active=True,
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    job = create_published_job(db_session, candidate.id)
    create_application(db_session, job.id, email=candidate.email)

    app.dependency_overrides[get_current_user] = lambda: candidate

    response = client.get("/api/v1/candidate/applications")

    assert response.status_code == 200
    envelope = response.json()
    assert envelope["success"] is True
    payload = envelope["data"]
    assert envelope["meta"]["request_id"] == response.headers["X-Request-ID"]
    assert payload["total"] == 1
    assert payload["items"][0]["job_id"] == str(job.id)
    assert payload["items"][0]["job_title"] == job.title
