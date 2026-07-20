import uuid
from datetime import UTC, date, datetime, timedelta

from platform_sdk.error_types import ValidationFailed
from pydantic import BaseModel

from app.core.enums import ServiceDeskPriority


class StatsFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    category_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None
    assignee_user_id: uuid.UUID | None = None
    priority: ServiceDeskPriority | None = None

    def validate_period(self) -> None:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationFailed("date_from не может быть позже date_to",
            )

    def boundaries(self) -> tuple[datetime | None, datetime | None]:
        self.validate_period()
        start = (
            datetime.combine(self.date_from, datetime.min.time(), UTC) if self.date_from else None
        )
        end = (
            datetime.combine(self.date_to + timedelta(days=1), datetime.min.time(), UTC)
            if self.date_to
            else None
        )
        return start, end


class DistributionItem(BaseModel):
    id: str
    label: str
    count: int


class SummaryRead(BaseModel):
    created: int
    closed_in_period: int
    current_backlog: int
    submitted: int
    pending_approval: int
    approved_in_period: int
    rejected_in_period: int
    assigned: int
    in_progress: int
    waiting_requester: int
    waiting_external: int
    resolved: int
    closed: int
    cancelled_in_period: int
    priorities: list[DistributionItem]


class DurationStats(BaseModel):
    average_seconds: float | None
    median_seconds: float | None
    p90_seconds: float | None
    sample_size: int


class TimeMetricsRead(BaseModel):
    time_to_approval: DurationStats
    time_to_assignment: DurationStats
    first_response_time: DurationStats
    resolution_time: DurationStats
    close_after_resolution_time: DurationStats


class SlaMetricsRead(BaseModel):
    response_compliance_percent: float | None
    resolution_compliance_percent: float | None
    response_breaches: int
    resolution_breaches: int
    active_near_breach: int
    active_breached: int


class BacklogBucket(BaseModel):
    code: str
    label: str
    count: int


class AssigneeStatsRow(BaseModel):
    user_id: uuid.UUID
    display_name: str
    is_active: bool
    currently_assigned: int
    in_progress: int
    waiting: int
    resolved_in_period: int
    closed_in_period: int
    breached_tickets: int
    median_resolution_seconds: float | None


class ApprovalMetricsRead(BaseModel):
    pending_approval_stages: int
    stage_duration: DurationStats
    rejection_rate_percent: float | None
