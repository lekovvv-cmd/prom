import uuid
from datetime import datetime

from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now


class ServiceDeskNotification(Base):
    __tablename__ = "service_desk_notifications"
    __table_args__ = (
        UniqueConstraint("event_id", "recipient_user_id", name="uq_sd_notification_event_recipient"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_desk_users.id"), nullable=False, index=True
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_desk_tickets.id"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ServiceDeskNotificationOutbox(Base):
    __tablename__ = "service_desk_notification_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", "channel", "recipient", name="uq_sd_outbox_event_channel_recipient"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
