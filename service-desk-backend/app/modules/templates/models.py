from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ApprovalMode, TemplateFieldType, TemplateVersionStatus, enum_values
from app.modules.catalog.models import ServiceDeskService


class ServiceDeskTemplateVersion(Base):
    __tablename__ = "service_desk_template_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_services.id"),
        index=True,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TemplateVersionStatus] = mapped_column(
        SAEnum(TemplateVersionStatus, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=TemplateVersionStatus.DRAFT,
    )
    approval_mode: Mapped[ApprovalMode] = mapped_column(
        SAEnum(ApprovalMode, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ApprovalMode.NONE,
    )
    default_assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        nullable=True,
    )
    system_settings: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service: Mapped[ServiceDeskService] = relationship()
    fields: Mapped[list["ServiceDeskTemplateField"]] = relationship(
        back_populates="template_version",
        cascade="all, delete-orphan",
        order_by="ServiceDeskTemplateField.position",
    )


class ServiceDeskTemplateField(Base):
    __tablename__ = "service_desk_template_fields"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_template_versions.id"),
        index=True,
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[TemplateFieldType] = mapped_column(
        SAEnum(TemplateFieldType, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    help_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    options: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    dictionary_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    visibility_rules: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    required_rules: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    template_version: Mapped[ServiceDeskTemplateVersion] = relationship(back_populates="fields")


class ServiceDeskDictionary(Base):
    __tablename__ = "service_desk_dictionaries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    items: Mapped[list["ServiceDeskDictionaryItem"]] = relationship(
        back_populates="dictionary",
        cascade="all, delete-orphan",
        order_by="ServiceDeskDictionaryItem.position",
    )


class ServiceDeskDictionaryItem(Base):
    __tablename__ = "service_desk_dictionary_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dictionary_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_dictionaries.id"),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    dictionary: Mapped[ServiceDeskDictionary] = relationship(back_populates="items")
