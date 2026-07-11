import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ServiceDeskAccessType


def _required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Field is required")
    return value


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _email(value: str) -> str:
    value = _required(value)
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("Invalid email")
    return value


class ServiceDeskUserRead(BaseModel):
    id: uuid.UUID
    identity_user_id: str
    email: str
    display_name: str
    department: str | None
    position: str | None
    access_type: ServiceDeskAccessType
    is_active: bool
    capabilities: list[str]
    created_at: datetime
    updated_at: datetime


class ServiceDeskCapabilitiesRead(BaseModel):
    capabilities: list[str]


class AccessUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity_user_id: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    access_type: ServiceDeskAccessType
    capabilities: list[str] = []

    @field_validator("identity_user_id", "display_name")
    @classmethod
    def strip_required(cls, value: str):
        return _required(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        return _email(value)

    @field_validator("department", "position")
    @classmethod
    def strip_optional(cls, value: str | None):
        return _optional(value)


class AccessUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = Field(default=None, min_length=3, max_length=255)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    access_type: ServiceDeskAccessType | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None):
        return _email(value) if value is not None else None

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str | None):
        return _required(value) if value is not None else None

    @field_validator("department", "position")
    @classmethod
    def strip_optional(cls, value: str | None):
        return _optional(value)


class CapabilityReplace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capabilities: list[str]


class AccessUserPage(BaseModel):
    items: list[ServiceDeskUserRead]
    page: int
    page_size: int
    total: int
    pages: int
