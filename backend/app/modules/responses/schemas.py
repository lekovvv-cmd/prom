from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ProjectResponseStatus
from app.core.security import is_utmn_email
from app.modules.attachments.schemas import AttachmentRead


class ProjectResponseCreate(BaseModel):
    full_name: str = Field(max_length=255)
    email: str
    comment: str | None = None
    competencies: str | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Укажите ФИО не короче 2 символов")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not is_utmn_email(normalized):
            raise ValueError("Разрешены только email на домене @utmn.ru")
        return normalized


class ProjectResponseRead(BaseModel):
    id: UUID
    project_id: UUID
    full_name: str
    email: str
    comment: str | None
    competencies: str | None
    attachments: list[AttachmentRead] = []
    status: ProjectResponseStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminProjectResponseRead(ProjectResponseRead):
    project_title: str
    processed_by: UUID | None
    processed_at: datetime | None


class ProjectResponseStatusUpdate(BaseModel):
    status: ProjectResponseStatus
