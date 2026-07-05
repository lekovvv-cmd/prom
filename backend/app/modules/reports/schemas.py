from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ReportPeriodStatus
from app.modules.users.schemas import UserRead


class ReportPeriodCreate(BaseModel):
    title: str = Field(max_length=255)
    starts_on: date | None = None
    ends_on: date | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Название периода должно быть не короче 3 символов")
        return normalized


class ReportPeriodRead(BaseModel):
    id: UUID
    title: str
    starts_on: date | None
    ends_on: date | None
    status: ReportPeriodStatus
    opened_by: UUID
    opened_at: datetime
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HalfYearReportPayload(BaseModel):
    completed_work: str
    project_results: str | None = None
    competencies_used: str | None = None
    difficulties: str | None = None
    next_period_plans: str | None = None

    @field_validator("completed_work")
    @classmethod
    def normalize_completed_work(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Опишите выполненную работу минимум 3 символами")
        return normalized

    @field_validator("project_results", "competencies_used", "difficulties", "next_period_plans")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class HalfYearReportRead(HalfYearReportPayload):
    id: UUID
    period_id: UUID
    user_id: UUID
    submitted_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminHalfYearReportRead(HalfYearReportRead):
    user: UserRead
    period: ReportPeriodRead


class CurrentReportState(BaseModel):
    active_period: ReportPeriodRead | None
    report: HalfYearReportRead | None
