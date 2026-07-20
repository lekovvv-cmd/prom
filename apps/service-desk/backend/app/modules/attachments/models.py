from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now
from app.core.enums import (
    ServiceDeskAttachmentOwnerType,
    ServiceDeskAttachmentStatus,
    enum_values,
)


class ServiceDeskAttachment(Base):
    __tablename__ = "service_desk_attachments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module: Mapped[str] = mapped_column(String(64), nullable=False, default="service-desk")
    owner_type: Mapped[ServiceDeskAttachmentOwnerType] = mapped_column(
        SAEnum(ServiceDeskAttachmentOwnerType, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_tickets.id"),
        nullable=False,
        index=True,
    )
    field_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    safe_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type_declared: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type_detected: Mapped[str | None] = mapped_column(String(255), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[ServiceDeskAttachmentStatus] = mapped_column(
        SAEnum(
            ServiceDeskAttachmentStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ServiceDeskAttachmentStatus.PENDING,
        index=True,
    )
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
