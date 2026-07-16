from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now


class ServiceDeskBusinessCalendar(Base):
    __tablename__ = "service_desk_business_calendars"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    business_hours: Mapped[list["ServiceDeskBusinessHours"]] = relationship(
        back_populates="calendar",
        cascade="all, delete-orphan",
        order_by=lambda: (ServiceDeskBusinessHours.weekday, ServiceDeskBusinessHours.start_time),
    )
    exceptions: Mapped[list["ServiceDeskCalendarException"]] = relationship(
        back_populates="calendar",
        cascade="all, delete-orphan",
        order_by=lambda: (
            ServiceDeskCalendarException.date,
            ServiceDeskCalendarException.start_time,
        ),
    )


class ServiceDeskBusinessHours(Base):
    __tablename__ = "service_desk_business_hours"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_business_calendars.id"),
        nullable=False,
        index=True,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    calendar: Mapped[ServiceDeskBusinessCalendar] = relationship(back_populates="business_hours")


class ServiceDeskCalendarException(Base):
    __tablename__ = "service_desk_calendar_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_business_calendars.id"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    calendar: Mapped[ServiceDeskBusinessCalendar] = relationship(back_populates="exceptions")


class ServiceDeskSlaPolicy(Base):
    __tablename__ = "service_desk_sla_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    business_calendar_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_desk_business_calendars.id"), nullable=False
    )
    first_response_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    pause_statuses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business_calendar: Mapped[ServiceDeskBusinessCalendar] = relationship()


class ServiceDeskSlaBinding(Base):
    __tablename__ = "service_desk_sla_bindings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_desk_sla_policies.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    policy: Mapped[ServiceDeskSlaPolicy] = relationship()


class ServiceDeskTicketSlaPause(Base):
    __tablename__ = "service_desk_ticket_sla_pauses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_desk_tickets.id"), nullable=False, index=True
    )
    reason_status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ServiceDeskEscalationRule(Base):
    __tablename__ = "service_desk_escalation_rules"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_policy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("service_desk_sla_policies.id"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("service_desk_users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ServiceDeskSlaEscalationEvent(Base):
    __tablename__ = "service_desk_sla_escalation_events"
    __table_args__ = (
        UniqueConstraint("ticket_id", "rule_id", name="uq_sla_escalation_ticket_rule"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("service_desk_tickets.id"), nullable=False, index=True)
    rule_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("service_desk_escalation_rules.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
