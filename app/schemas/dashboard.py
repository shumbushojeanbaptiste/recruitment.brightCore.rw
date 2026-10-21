from pydantic import BaseModel


class DashboardSummary(BaseModel):
    published_jobs: int
    total_applications: int
    pending_reviews: int
    accepted_applications: int
    rejected_applications: int