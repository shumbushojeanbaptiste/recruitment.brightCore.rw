from app.api.deps import require_admin

from tests.helpers import create_published_job, create_user


def test_admin_job_list_returns_all_jobs_as_a_list(client, db_session):
    admin = create_user(db_session)
    first_job = create_published_job(db_session, admin.id)
    second_job = create_published_job(db_session, admin.id)

    client.app.dependency_overrides[require_admin] = lambda: admin

    response = client.get("/api/v1/admin/jobs")

    assert response.status_code == 200
    envelope = response.json()
    assert envelope["success"] is True
    jobs = envelope["data"]
    assert isinstance(jobs, list)
    assert len(jobs) == 2
    assert {job["id"] for job in jobs} == {
        str(first_job.id),
        str(second_job.id),
    }
