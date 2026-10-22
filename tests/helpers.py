
import uuid
from datetime import datetime, timezone

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.core.security import hash_password




def create_user(
    db,
    *,
    email="admin@example.com",
    role="admin",
    password="TestPassword-123!",
):
    user = User(
        id=uuid.uuid4(),
        full_name="Test Administrator",
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_published_job(db, created_by):
    now = datetime.now(timezone.utc)

    job = Job(
        id=uuid.uuid4(),
        title="Backend Engineer",
        department="Engineering",
        location="Kigali",
        employment_type="full_time",
        description="Build and maintain APIs.",
        requirements="Python and SQLAlchemy experience.",
        salary_min=500000,
        salary_max=1000000,
        status="published",
        published_at=now,
        expires_at=None,
        created_by=created_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_application(db, job_id, email="candidate@example.com"):
    application = Application(
        id=uuid.uuid4(),
        job_id=job_id,
        full_name="Test Candidate",
        email=email,
        phone="+250788000000",
        cover_note="I am interested in this role.",
        cv_storage_key=f"{uuid.uuid4().hex}.pdf",
        cv_original_filename="resume.pdf",
        cv_size_bytes=1024,
        cv_sha256="a" * 64,
        status="submitted",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application
