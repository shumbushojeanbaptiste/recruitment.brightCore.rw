
import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

EmploymentType = Literal[
    "full_time",
    "part_time",
    "contract",
    "internship",
    "temporary",
]


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    department: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=160)
    employment_type: EmploymentType
    description: str = Field(min_length=30, max_length=30000)
    requirements: str = Field(min_length=10, max_length=20000)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    expires_at: datetime | None = None

    @field_validator(
        "title", "department", "location", "description", "requirements"
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_job(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError(
                "salary_max must be greater than or equal to salary_min"
            )

        if self.expires_at is not None and self.expires_at.utcoffset() is None:
            raise ValueError("expires_at must include a timezone")

        return self


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    department: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, min_length=2, max_length=160)
    employment_type: EmploymentType | None = None
    description: str | None = Field(default=None, min_length=30, max_length=30000)
    requirements: str | None = Field(default=None, min_length=10, max_length=20000)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    expires_at: datetime | None = None

    @field_validator(
        "title", "department", "location", "description", "requirements"
    )
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_update(self):
        if self.expires_at is not None and self.expires_at.utcoffset() is None:
            raise ValueError("expires_at must include a timezone")

        return self


class JobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    department: str
    location: str
    employment_type: str
    description: str
    requirements: str
    salary_min: int | None
    salary_max: int | None
    status: str
    published_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JobAdmin(JobPublic):
    created_by: uuid.UUID


class JobListResponse(BaseModel):
    items: list[JobPublic]
    page: int
    page_size: int
    total: int
    pages: int
