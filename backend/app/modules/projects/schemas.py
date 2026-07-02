from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ProjectMemberRole, ProjectPriority, ProjectStatus, ProjectType
from app.modules.users.schemas import UserShort


class ProjectMemberRead(BaseModel):
    id: UUID
    full_name: str
    email: str
    member_role: ProjectMemberRole


class ProjectBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    short_description: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=3)
    goal: str = Field(min_length=3)
    expected_result: str | None = None
    project_type: ProjectType = ProjectType.STRATEGIC
    priority: ProjectPriority = ProjectPriority.MEDIUM
    status: ProjectStatus = ProjectStatus.DRAFT
    start_date: date | None = None
    end_date: date | None = None
    responsible_user_id: UUID | None = None
    contact_email: str | None = None
    required_competencies: str | None = None
    planned_tasks: str | None = None

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = value.strip().lower()
        if not normalized.endswith("@utmn.ru"):
            raise ValueError("Разрешены только email на домене @utmn.ru")
        return normalized


class ProjectCreate(ProjectBase):
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    short_description: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = Field(default=None, min_length=3)
    goal: str | None = Field(default=None, min_length=3)
    expected_result: str | None = None
    project_type: ProjectType | None = None
    priority: ProjectPriority | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    responsible_user_id: UUID | None = None
    contact_email: str | None = None
    required_competencies: str | None = None
    planned_tasks: str | None = None

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = value.strip().lower()
        if not normalized.endswith("@utmn.ru"):
            raise ValueError("Разрешены только email на домене @utmn.ru")
        return normalized


class ProjectSummary(BaseModel):
    id: UUID
    title: str
    short_description: str
    goal: str
    project_type: ProjectType
    priority: ProjectPriority
    status: ProjectStatus
    start_date: date | None
    end_date: date | None
    responsible: UserShort | None
    responses_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetails(ProjectSummary):
    description: str
    expected_result: str | None
    contact_email: str | None
    members: list[ProjectMemberRead]
    required_competencies: str | None
    planned_tasks: str | None
    updated_at: datetime


class OkResponse(BaseModel):
    ok: bool
