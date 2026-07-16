from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ReportPeriodStatus

if TYPE_CHECKING:
    from app.modules.users.models import User


def enum_values(enum_class: type) -> list[str]:
    return [item.value for item in enum_class]


class ReportPeriod(Base):
    __tablename__ = "report_periods"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ReportPeriodStatus] = mapped_column(
        SAEnum(ReportPeriodStatus, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ReportPeriodStatus.OPEN,
        index=True,
    )
    opened_by: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    opener: Mapped["User"] = relationship("User", foreign_keys=[opened_by])
    reports: Mapped[list["HalfYearReport"]] = relationship(
        "HalfYearReport", back_populates="period", cascade="all, delete-orphan"
    )


class HalfYearReport(Base):
    __tablename__ = "half_year_reports"
    __table_args__ = (UniqueConstraint("period_id", "user_id", name="uq_half_year_report_period_user"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("report_periods.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    completed_work: Mapped[str] = mapped_column(Text, nullable=False)
    project_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    competencies_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulties: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_period_plans: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    period: Mapped[ReportPeriod] = relationship("ReportPeriod", back_populates="reports")
    user: Mapped["User"] = relationship("User")
