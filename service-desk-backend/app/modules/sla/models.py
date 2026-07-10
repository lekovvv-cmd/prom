from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now


class ServiceDeskBusinessCalendar(Base):
    __tablename__ = "service_desk_business_calendars"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
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
