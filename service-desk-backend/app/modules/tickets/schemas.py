import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ServiceDeskPriority, ServiceDeskTicketStatus


class TicketDraftCreate(BaseModel):
    service_id: uuid.UUID
    requester_user_id: uuid.UUID
    template_version_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    priority: ServiceDeskPriority = ServiceDeskPriority.MEDIUM
    field_values: dict[str, Any] = Field(default_factory=dict)


class TicketDraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    priority: ServiceDeskPriority | None = None
    field_values: dict[str, Any] | None = None


class TicketActorAction(BaseModel):
    actor_user_id: uuid.UUID


class TicketCommentAction(TicketActorAction):
    comment: str = Field(min_length=2, max_length=2000)


class TicketReasonAction(TicketActorAction):
    reason: str = Field(min_length=2, max_length=2000)


class TicketResolveAction(TicketActorAction):
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


class TicketRead(BaseModel):
    id: uuid.UUID
    number: str | None
    service_id: uuid.UUID
    template_version_id: uuid.UUID
    requester_user_id: uuid.UUID
    assignee_user_id: uuid.UUID | None
    title: str
    description: str | None
    status: ServiceDeskTicketStatus
    priority: ServiceDeskPriority
    field_values: dict[str, Any]
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
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    history: list[TicketHistoryRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
