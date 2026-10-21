
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'closed')",
            name="ck_jobs_status",
        ),
        CheckConstraint(
            "employment_type IN ('full_time', 'part_time', "
            "'contract', 'internship', 'temporary')",
            name="ck_jobs_employment_type",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_min >= 0",
            name="ck_jobs_salary_min_nonnegative",
        ),
        CheckConstraint(
            "salary_max IS NULL OR salary_max >= 0",
            name="ck_jobs_salary_max_nonnegative",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL "
            "OR salary_max >= salary_min",
            name="ck_jobs_salary_range",
        ),
        Index("ix_jobs_status_created_at", "status", "created_at"),
        Index("ix_jobs_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    employment_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)

    salary_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    salary_max: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
