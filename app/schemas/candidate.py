
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


ApplicationStatus = Literal[
    "submitted",
    "under_review",
    "accepted",
    "rejected",
]


class CandidateApplicationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    job_title: str
    full_name: str
    email: str
    status: ApplicationStatus
    status_note: str | None = None
    created_at: datetime
    updated_at: datetime



class CandidateApplicationListResponse(BaseModel):
    items: list[CandidateApplicationItem]
    total: int
