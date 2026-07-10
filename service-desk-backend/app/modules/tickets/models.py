from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ServiceDeskPriority, ServiceDeskTicketStatus, enum_values
from app.modules.access.models import ServiceDeskUser
from app.modules.catalog.models import ServiceDeskService
from app.modules.templates.models import ServiceDeskTemplateVersion

if TYPE_CHECKING:
    from app.modules.approvals.models import ServiceDeskTicketApprovalStage
    from app.modules.comments.models import ServiceDeskTicketComment


class ServiceDeskTicket(Base):
    __tablename__ = "service_desk_tickets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    service_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_services.id"),
        index=True,
        nullable=False,
    )
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_template_versions.id"),
        nullable=False,
    )
    requester_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        index=True,
        nullable=False,
    )
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ServiceDeskTicketStatus] = mapped_column(
        SAEnum(ServiceDeskTicketStatus, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ServiceDeskTicketStatus.DRAFT,
        index=True,
    )
    priority: Mapped[ServiceDeskPriority] = mapped_column(
        SAEnum(ServiceDeskPriority, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ServiceDeskPriority.MEDIUM,
        index=True,
    )
    field_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    work_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    sla_policy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    first_response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    resolution_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_breached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_breached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_response_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_resolution_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    paused_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    routing_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    service: Mapped[ServiceDeskService] = relationship()
    template_version: Mapped[ServiceDeskTemplateVersion] = relationship()
    requester: Mapped[ServiceDeskUser] = relationship(foreign_keys=[requester_user_id])
    assignee: Mapped[ServiceDeskUser | None] = relationship(foreign_keys=[assignee_user_id])
    history: Mapped[list["ServiceDeskTicketHistory"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ServiceDeskTicketHistory.created_at",
    )
    approval_stages: Mapped[list["ServiceDeskTicketApprovalStage"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ServiceDeskTicketApprovalStage.position",
    )
    comments: Mapped[list["ServiceDeskTicketComment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ServiceDeskTicketComment.created_at",
    )


class ServiceDeskTicketHistory(Base):
    __tablename__ = "service_desk_ticket_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_tickets.id"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    ticket: Mapped[ServiceDeskTicket] = relationship(back_populates="history")
    actor: Mapped[ServiceDeskUser | None] = relationship()


class ServiceDeskTicketCounter(Base):
    __tablename__ = "service_desk_ticket_counters"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
