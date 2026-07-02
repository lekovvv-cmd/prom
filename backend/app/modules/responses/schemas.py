from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ProjectResponseStatus


class ProjectResponseCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str
    comment: str | None = None
    competencies: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized.endswith("@utmn.ru"):
            raise ValueError("Разрешены только email на домене @utmn.ru")
        return normalized


class ProjectResponseRead(BaseModel):
    id: UUID
    project_id: UUID
    full_name: str
    email: str
    comment: str | None
    competencies: str | None
    status: ProjectResponseStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminProjectResponseRead(ProjectResponseRead):
    project_title: str
    processed_by: UUID | None
    processed_at: datetime | None


class ProjectResponseStatusUpdate(BaseModel):
    status: ProjectResponseStatus
