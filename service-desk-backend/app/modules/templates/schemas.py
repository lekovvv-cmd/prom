import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TemplateVersionStatus


DEFAULT_SYSTEM_SETTINGS = {
    "default_title": None,
    "is_title_editable": True,
    "is_description_required": True,
    "help_text": None,
}


class TemplateVersionCreate(BaseModel):
    system_settings: dict[str, Any] = Field(default_factory=lambda: dict(DEFAULT_SYSTEM_SETTINGS))


class TemplateVersionUpdate(BaseModel):
    system_settings: dict[str, Any] | None = None


class TemplateVersionRead(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    version: int
    status: TemplateVersionStatus
    system_settings: dict[str, Any]
    created_by: uuid.UUID | None
    published_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PublishedTemplateRead(BaseModel):
    service_id: uuid.UUID
    template_version: TemplateVersionRead
    fields: list[dict[str, Any]] = Field(default_factory=list)
