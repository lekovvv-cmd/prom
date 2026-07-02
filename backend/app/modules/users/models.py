from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import UserRole


def enum_values(enum_class: type) -> list[str]:
    return [item.value for item in enum_class]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=UserRole.EMPLOYEE,
    )
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    created_projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="creator", foreign_keys="Project.created_by"
    )
    responsible_projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="responsible", foreign_keys="Project.responsible_user_id"
    )
