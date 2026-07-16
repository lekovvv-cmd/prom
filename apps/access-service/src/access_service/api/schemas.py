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


class ModuleOut(BaseModel):
    id: str
    permissions: list[str]


class SessionOut(BaseModel):
    user: UserOut
    modules: list[ModuleOut]
    permissions: list[str]


class RoleOut(BaseModel):
    id: str
    code: str
    title: str
    permissions: list[str]


class RoleInput(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9_.-]+$")
    title: str = Field(min_length=2, max_length=255)
    permissions: list[str] = Field(default_factory=list)


class UserRolesInput(BaseModel):
    role_codes: list[str]


class MockLoginInput(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    session: SessionOut
