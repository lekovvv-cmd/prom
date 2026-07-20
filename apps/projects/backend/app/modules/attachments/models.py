from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now
from app.core.enums import AttachmentOwnerType, AttachmentStatus


def enum_values(enum_class: type[Enum]) -> list[str]:
    return [item.value for item in enum_class]


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module: Mapped[str] = mapped_column(String(64), nullable=False, default="projects")
    owner_type: Mapped[AttachmentOwnerType] = mapped_column(
        SAEnum(AttachmentOwnerType, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        unique=True,
        index=True,
    )
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    safe_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type_declared: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type_detected: Mapped[str | None] = mapped_column(String(255), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[AttachmentStatus] = mapped_column(
        SAEnum(
            AttachmentStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AttachmentStatus.PENDING,
        index=True,
    )
    size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
