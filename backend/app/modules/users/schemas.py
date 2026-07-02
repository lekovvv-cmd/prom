from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import UserRole


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    department: str | None = None
    position: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserShort(BaseModel):
    id: UUID
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


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
