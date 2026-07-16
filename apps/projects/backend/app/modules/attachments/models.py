from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now
from app.core.enums import AttachmentOwnerType


def enum_values(enum_class: type) -> list[str]:
    return [item.value for item in enum_class]


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[AttachmentOwnerType] = mapped_column(
        SAEnum(AttachmentOwnerType, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
