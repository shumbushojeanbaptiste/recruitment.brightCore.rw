import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ApplicationStatusHistoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    previous_status: str | None
    new_status: str
    note: str | None
    changed_by: uuid.UUID | None
    changed_at: datetime


class AuditEventPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    created_at: datetime


class AuditEventListResponse(BaseModel):
    items: list[AuditEventPublic]
    page: int
    page_size: int
    total: int
    pages: int