import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import ServiceDeskAccessType


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
    identity_user_id: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    access_type: ServiceDeskAccessType
    capabilities: list[str] = []

    @field_validator("identity_user_id", "email", "display_name")
    @classmethod
    def strip_required(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Поле обязательно")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Некорректный email")
        return value


class AccessUserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    access_type: ServiceDeskAccessType | None = None
    capabilities: list[str] | None = None


class CapabilityReplace(BaseModel):
    capabilities: list[str]


class AccessUserPage(BaseModel):
    items: list[ServiceDeskUserRead]
    page: int
    page_size: int
    total: int
    pages: int
