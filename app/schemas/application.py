
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ApplicationStatus = Literal[
    "submitted",
    "under_review",
    "accepted",
    "rejected",
]


class ApplicationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: str
    cover_note: str | None
    cv_original_filename: str
    cv_size_bytes: int
    status: str
    status_note: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: str | None = Field(default=None, max_length=5000)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationPublic]
    page: int
    page_size: int
    total: int
    pages: int
