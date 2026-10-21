
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "email",
            name="uq_applications_job_email",
        ),
        CheckConstraint(
            "status IN ('submitted', 'under_review', 'accepted', 'rejected')",
            name="ck_applications_status",
        ),
        Index("ix_applications_job_created", "job_id", "created_at"),
        Index("ix_applications_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    cover_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cv_storage_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cv_original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cv_size_bytes: Mapped[int] = mapped_column(
        nullable=False,
    )
    cv_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="submitted",
        server_default="submitted",
    )
    status_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
