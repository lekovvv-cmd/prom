from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ProjectTaskStatus
from app.modules.attachments.schemas import AttachmentRead
from app.modules.users.schemas import UserShort


class ProjectStageBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    position: int = 0
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        title = value.strip()
        if len(title) < 2:
            raise ValueError("Название этапа должно быть не короче 2 символов")
        return title


class ProjectStageCreate(ProjectStageBase):
    pass


class ProjectStageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    position: int | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if len(title) < 2:
            raise ValueError("Название этапа должно быть не короче 2 символов")
        return title


class ProjectTaskBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    stage_id: UUID | None = None
    assignee_user_id: UUID | None = None
    status: ProjectTaskStatus = ProjectTaskStatus.TODO
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        title = value.strip()
        if len(title) < 2:
            raise ValueError("Название задачи должно быть не короче 2 символов")
        return title

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        return value.strip() or None


class ProjectTaskCreate(ProjectTaskBase):
    pass


class ProjectTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    stage_id: UUID | None = None
    assignee_user_id: UUID | None = None
    status: ProjectTaskStatus | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if len(title) < 2:
            raise ValueError("Название задачи должно быть не короче 2 символов")
        return title

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        return value.strip() or None


class ProjectTaskStatusUpdate(BaseModel):
    status: ProjectTaskStatus


class ProjectTaskRead(BaseModel):
    id: UUID
    project_id: UUID
    stage_id: UUID | None
    title: str
    description: str | None
    assignee: UserShort | None
    status: ProjectTaskStatus
    due_date: date | None
    is_overdue: bool
    attachments: list[AttachmentRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectStageRead(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    position: int
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectStageWithTasksRead(ProjectStageRead):
    tasks: list[ProjectTaskRead] = Field(default_factory=list)
