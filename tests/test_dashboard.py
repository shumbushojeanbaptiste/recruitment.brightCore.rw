
from app.services.dashboard_service import get_dashboard_summary

from tests.helpers import (
    create_application,
    create_published_job,
    create_user,
)


def test_dashboard_counts_applications_by_status(db_session):
    admin = create_user(db_session)
    job = create_published_job(db_session, admin.id)

    create_application(
        db_session,
        job.id,
        email="candidate1@example.com",
    )
    accepted = create_application(
        db_session,
        job.id,
        email="candidate2@example.com",
    )
    rejected = create_application(
        db_session,
        job.id,
        email="candidate3@example.com",
    )

    accepted.status = "accepted"
    rejected.status = "rejected"
    db_session.commit()

    summary = get_dashboard_summary(db_session)

    assert summary["published_jobs"] == 1
    assert summary["total_applications"] == 3
    assert summary["pending_reviews"] == 1
    assert summary["accepted_applications"] == 1
    assert summary["rejected_applications"] == 1


def test_dashboard_endpoint_requires_authentication(client):
    response = client.get("/api/v1/admin/dashboard/summary")

    assert response.status_code in (401, 403)
    envelope = response.json()
    assert envelope["success"] is False
    assert envelope["error"]["code"] in {"unauthorized", "forbidden"}
    assert envelope["meta"]["request_id"] == response.headers["X-Request-ID"]
