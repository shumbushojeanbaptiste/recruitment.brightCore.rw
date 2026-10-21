from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job


def get_dashboard_summary(db: Session) -> dict:
    published_jobs = db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.status == "published")
    ) or 0

    total_applications = db.scalar(
        select(func.count()).select_from(Application)
    ) or 0

    pending_reviews = db.scalar(
        select(func.count())
        .select_from(Application)
        .where(
            Application.status.in_(["submitted", "under_review"])
        )
    ) or 0

    accepted = db.scalar(
        select(func.count())
        .select_from(Application)
        .where(Application.status == "accepted")
    ) or 0

    rejected = db.scalar(
        select(func.count())
        .select_from(Application)
        .where(Application.status == "rejected")
    ) or 0

    return {
        "published_jobs": published_jobs,
        "total_applications": total_applications,
        "pending_reviews": pending_reviews,
        "accepted_applications": accepted,
        "rejected_applications": rejected,
    }