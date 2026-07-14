import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    position: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    position: int | None = None
    is_active: bool | None = None


class CategoryRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    parent_id: uuid.UUID | None
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ServiceCreate(BaseModel):
    category_id: uuid.UUID
    default_assignee_user_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    position: int = 0
    is_active: bool = True


class ServiceUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    default_assignee_user_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    position: int | None = None
    is_active: bool | None = None


class ServiceRead(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    default_assignee_user_id: uuid.UUID | None
    title: str
    short_description: str | None
    description: str | None
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    category: CategoryRead | None = None
    request_form_available: bool = False

    model_config = ConfigDict(from_attributes=True)
