from __future__ import annotations

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: str
    external_subject: str | None
    email: str
    display_name: str
    department: str | None
    position: str | None
    is_active: bool
    session_version: int


class ModuleOut(BaseModel):
    id: str
    permissions: list[str]


class ModuleAdminOut(BaseModel):
    id: str
    title: str
    is_active: bool


class ModuleInput(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$")
    title: str = Field(min_length=2, max_length=255)


class SessionOut(BaseModel):
    user: UserOut
    modules: list[ModuleOut]
    permissions: list[str]


class RoleOut(BaseModel):
    id: str
    code: str
    title: str
    module_id: str | None
    permissions: list[str]


class RoleInput(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9_.-]+$")
    title: str = Field(min_length=2, max_length=255)
    module_id: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$")
    permissions: list[str] = Field(default_factory=list)


class UserRolesInput(BaseModel):
    role_codes: list[str]


class MockLoginInput(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    code: str = Field(min_length=6, max_length=32)


class MockCodeInput(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MockCodeOut(BaseModel):
    email: str
    dev_code: str


class GroupInput(BaseModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_.-]{1,126}[a-z0-9]$")
    title: str = Field(min_length=2, max_length=255)


class GroupOut(BaseModel):
    id: str
    code: str
    title: str
    member_ids: list[str]
    role_codes: list[str]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    session: SessionOut


class SessionProbeOut(BaseModel):
    authenticated: bool
    token: TokenOut | None = None
