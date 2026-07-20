from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ProjectMemberRole, ProjectPriority, ProjectStatus, ProjectType, UserRole
from app.core.security import is_utmn_email
from app.modules.attachments.schemas import AttachmentRead
from app.modules.users.schemas import UserShort


class ProjectMemberRead(BaseModel):
    id: UUID
    full_name: str
    email: str
    member_role: ProjectMemberRole


class ProjectCompetencyBlock(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    competencies: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Название направления должно быть не короче 2 символов")
        return normalized

    @field_validator("competencies")
    @classmethod
    def normalize_competencies(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            competency = item.strip()
            key = competency.casefold()
            if not competency or key in seen:
                continue
            seen.add(key)
            normalized.append(competency)
        return normalized


class ProjectCompetencyCoverage(BaseModel):
    block_title: str
    competency: str
    accepted_count: int
    is_covered: bool
    priority: Literal["open", "covered"]


class ProjectCandidateRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    department: str | None = None
    position: str | None = None
    competencies: str | None = None
    about: str | None = None
    matched_competencies: list[str] = Field(default_factory=list)
    matched_blocks: list[str] = Field(default_factory=list)
    match_score: int = 0
    is_working_group_member: bool = False
    has_response: bool = False


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
    working_group_member_ids: list[UUID] = Field(default_factory=list)
    contact_email: str | None = None
    required_competencies: str | None = None
    competency_blocks: list[ProjectCompetencyBlock] = Field(default_factory=list)
    planned_tasks: str | None = None

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = value.strip().lower()
        if not is_utmn_email(normalized):
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
    working_group_member_ids: list[UUID] | None = None
    contact_email: str | None = None
    required_competencies: str | None = None
    competency_blocks: list[ProjectCompetencyBlock] | None = None
    planned_tasks: str | None = None

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = value.strip().lower()
        if not is_utmn_email(normalized):
            raise ValueError("Разрешены только email на домене @utmn.ru")
        return normalized


class ProjectSummary(BaseModel):
    id: UUID
    version: int
    title: str
    short_description: str
    goal: str
    project_type: ProjectType
    priority: ProjectPriority
    status: ProjectStatus
    start_date: date | None
    end_date: date | None
    responsible: UserShort | None
    required_competencies: str | None
    competency_blocks: list[ProjectCompetencyBlock] = Field(default_factory=list)
    responses_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectRecommendationRead(BaseModel):
    project: ProjectSummary
    score: int
    matched_competencies: list[str] = Field(default_factory=list)
    matched_blocks: list[str] = Field(default_factory=list)
    matched_profile_terms: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class ProjectDetails(ProjectSummary):
    description: str
    expected_result: str | None
    contact_email: str | None
    members: list[ProjectMemberRead]
    attachments: list[AttachmentRead]
    required_competencies: str | None
    competency_coverage: list[ProjectCompetencyCoverage] = Field(default_factory=list)
    planned_tasks: str | None
    updated_at: datetime


class OkResponse(BaseModel):
    ok: bool
