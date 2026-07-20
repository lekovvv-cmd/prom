from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ProjectMemberRole, ProjectPriority, ProjectStatus, ProjectType

if TYPE_CHECKING:
    from app.modules.responses.models import ProjectResponse
    from app.modules.users.models import User


def enum_values(enum_class: type[Enum]) -> list[str]:
    return [item.value for item in enum_class]


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[ProjectType] = mapped_column(
        SAEnum(ProjectType, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ProjectType.STRATEGIC,
    )
    priority: Mapped[ProjectPriority] = mapped_column(
        SAEnum(ProjectPriority, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ProjectPriority.MEDIUM,
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ProjectStatus.DRAFT,
        index=True,
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required_competencies: Mapped[str | None] = mapped_column(Text, nullable=True)
    competency_blocks: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    planned_tasks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    creator: Mapped["User"] = relationship(
        "User", back_populates="created_projects", foreign_keys=[created_by]
    )
    responsible: Mapped["User | None"] = relationship(
        "User", back_populates="responsible_projects", foreign_keys=[responsible_user_id]
    )
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    responses: Mapped[list["ProjectResponse"]] = relationship("ProjectResponse", back_populates="project")
    tags: Mapped[list["ProjectTagLink"]] = relationship(
        "ProjectTagLink", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    member_role: Mapped[ProjectMemberRole] = mapped_column(
        SAEnum(ProjectMemberRole, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ProjectMemberRole.PARTICIPANT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User")


class ProjectTag(Base):
    __tablename__ = "project_tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    links: Mapped[list["ProjectTagLink"]] = relationship(
        "ProjectTagLink", back_populates="tag", cascade="all, delete-orphan"
    )


class ProjectTagLink(Base):
    __tablename__ = "project_tag_links"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("project_tags.id"), primary_key=True)

    project: Mapped[Project] = relationship("Project", back_populates="tags")
    tag: Mapped[ProjectTag] = relationship("ProjectTag", back_populates="links")
