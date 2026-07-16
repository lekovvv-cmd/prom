from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import UserRole


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    department: str | None = None
    position: str | None = None
    competencies: str | None = None
    about: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserShort(BaseModel):
    id: UUID
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    full_name: str = Field(max_length=255)
    department: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    competencies: str | None = None
    about: str | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("ФИО должно быть не короче 2 символов")
        return normalized

    @field_validator("department", "position", "competencies", "about")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class AuthEmailRequest(BaseModel):
    email: str


class AuthVerifyRequest(BaseModel):
    email: str
    code: str


class AuthCodeResponse(BaseModel):
    email: str
    dev_code: str
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
