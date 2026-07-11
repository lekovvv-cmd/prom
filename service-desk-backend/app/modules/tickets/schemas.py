import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ServiceDeskPriority, ServiceDeskTicketStatus
from app.modules.approvals.schemas import TicketApprovalStageRead


class TicketUserSummary(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TicketCategorySummary(BaseModel):
    id: uuid.UUID
    title: str

    model_config = ConfigDict(from_attributes=True)


class TicketServiceSummary(BaseModel):
    id: uuid.UUID
    title: str
    category: TicketCategorySummary

    model_config = ConfigDict(from_attributes=True)


class StrictTicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TicketDraftCreate(StrictTicketRequest):
    service_id: uuid.UUID
    template_version_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    priority: ServiceDeskPriority = ServiceDeskPriority.MEDIUM
    field_values: dict[str, Any] = Field(default_factory=dict)


class TicketDraftUpdate(StrictTicketRequest):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    priority: ServiceDeskPriority | None = None
    field_values: dict[str, Any] | None = None


class TicketAction(StrictTicketRequest):
    pass


class TicketAssignmentAction(StrictTicketRequest):
    assignee_user_id: uuid.UUID


class TicketCommentAction(StrictTicketRequest):
    comment: str = Field(min_length=2, max_length=2000)


class TicketReasonAction(StrictTicketRequest):
    reason: str = Field(min_length=2, max_length=2000)


class TicketResolveAction(StrictTicketRequest):
    resolution_summary: str = Field(min_length=2, max_length=5000)
    comment: str | None = Field(default=None, max_length=2000)


class TicketHistoryRead(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    event_type: str
    actor_user_id: uuid.UUID | None
    message: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketFieldSnapshotRead(BaseModel):
    label: str
    type: str
    raw_value: Any
    display_value: str


class TicketCommentSummary(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_user_id: uuid.UUID
    author: TicketUserSummary
    body: str
    visibility: Literal["public", "internal"]
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TicketRead(BaseModel):
    id: uuid.UUID
    number: str | None
    service_id: uuid.UUID
    service: TicketServiceSummary
    template_version_id: uuid.UUID
    requester_user_id: uuid.UUID
    requester: TicketUserSummary
    assignee_user_id: uuid.UUID | None
    assignee: TicketUserSummary | None
    title: str
    description: str | None
    status: ServiceDeskTicketStatus
    priority: ServiceDeskPriority
    field_values: dict[str, Any]
    field_snapshot: list[TicketFieldSnapshotRead] = Field(default_factory=list)
    routing_snapshot: dict[str, Any] | None
    sla_snapshot: dict[str, Any] | None
    sla_policy_id: uuid.UUID | None
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    first_response_at: datetime | None
    response_breached_at: datetime | None
    resolution_breached_at: datetime | None
    is_response_breached: bool
    is_resolution_breached: bool
    paused_seconds: int
    submitted_at: datetime | None
    approval_started_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    assigned_at: datetime | None
    work_started_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    cancelled_at: datetime | None
    resolution_summary: str | None
    cancellation_reason: str | None
    approval_stages: list[TicketApprovalStageRead] = Field(default_factory=list)
    comments: list[TicketCommentSummary] = Field(default_factory=list)
    allowed_actions: list[Literal[
        "approve", "reject", "assign", "reassign", "start", "request_clarification",
        "wait_external", "resume", "resolve", "close", "cancel",
    ]] = Field(
        default_factory=list
    )
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    history: list[TicketHistoryRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
