import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TemplateFieldType, TemplateVersionStatus


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


class TemplateFieldCreate(BaseModel):
    key: str = Field(min_length=2, max_length=128, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    label: str = Field(min_length=2, max_length=255)
    field_type: TemplateFieldType
    is_required: bool = False
    position: int = 0
    help_text: str | None = Field(default=None, max_length=500)
    placeholder: str | None = Field(default=None, max_length=255)
    options: list[dict[str, Any]] | None = None
    dictionary_code: str | None = Field(default=None, max_length=128)
    validation: dict[str, Any] | None = None
    visibility_rules: dict[str, Any] | None = None
    required_rules: dict[str, Any] | None = None


class TemplateFieldUpdate(BaseModel):
    key: str | None = Field(default=None, min_length=2, max_length=128, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    label: str | None = Field(default=None, min_length=2, max_length=255)
    field_type: TemplateFieldType | None = None
    is_required: bool | None = None
    position: int | None = None
    help_text: str | None = Field(default=None, max_length=500)
    placeholder: str | None = Field(default=None, max_length=255)
    options: list[dict[str, Any]] | None = None
    dictionary_code: str | None = Field(default=None, max_length=128)
    validation: dict[str, Any] | None = None
    visibility_rules: dict[str, Any] | None = None
    required_rules: dict[str, Any] | None = None


class TemplateFieldRead(BaseModel):
    id: uuid.UUID
    template_version_id: uuid.UUID
    key: str
    label: str
    field_type: TemplateFieldType
    is_required: bool
    position: int
    help_text: str | None
    placeholder: str | None
    options: list[dict[str, Any]] | None
    dictionary_code: str | None
    validation: dict[str, Any] | None
    visibility_rules: dict[str, Any] | None
    required_rules: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateFieldsReorder(BaseModel):
    field_ids: list[uuid.UUID]


class TemplateValidationRequest(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class TemplateValidationErrorItem(BaseModel):
    field_key: str
    message: str


class TemplateValidationResult(BaseModel):
    is_valid: bool
    errors: list[TemplateValidationErrorItem]
    visible_fields: list[str]
    required_fields: list[str]
    normalized_data: dict[str, Any]


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
    fields: list[TemplateFieldRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PublishedTemplateRead(BaseModel):
    service_id: uuid.UUID
    template_version: TemplateVersionRead
    fields: list[TemplateFieldRead] = Field(default_factory=list)


class DictionaryItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=255)
    position: int = 0
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class DictionaryItemUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    value: str | None = Field(default=None, min_length=1, max_length=255)
    position: int | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class DictionaryItemRead(BaseModel):
    id: uuid.UUID
    dictionary_id: uuid.UUID
    label: str
    value: str
    position: int
    is_active: bool
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DictionaryCreate(BaseModel):
    code: str = Field(min_length=2, max_length=128, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class DictionaryUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=128, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class DictionaryRead(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[DictionaryItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
