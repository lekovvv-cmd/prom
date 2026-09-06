from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ProjectResponseStatus

if TYPE_CHECKING:
    from app.modules.projects.models import Project
    from app.modules.users.models import User


def enum_values(enum_class: type[Enum]) -> list[str]:
    return [item.value for item in enum_class]


class ProjectResponse(Base):
    __tablename__ = "project_responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    competencies: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectResponseStatus] = mapped_column(
        SAEnum(ProjectResponseStatus, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ProjectResponseStatus.NEW,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    processed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    __table_args__ = (
        Index(
            "uq_project_responses_active_project_email",
            project_id,
            func.lower(email),
            unique=True,
            postgresql_where=(status != ProjectResponseStatus.CANCELLED) & deleted_at.is_(None),
            sqlite_where=(status != ProjectResponseStatus.CANCELLED) & deleted_at.is_(None),
        ),
        Index(
            "uq_project_responses_active_project_user",
            project_id,
            user_id,
            unique=True,
            postgresql_where=(
                user_id.is_not(None)
                & (status != ProjectResponseStatus.CANCELLED)
                & deleted_at.is_(None)
            ),
            sqlite_where=(
                user_id.is_not(None)
                & (status != ProjectResponseStatus.CANCELLED)
                & deleted_at.is_(None)
            ),
        ),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="responses")
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    processor: Mapped["User | None"] = relationship("User", foreign_keys=[processed_by])
