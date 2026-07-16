from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ApprovalDecisionRule, ServiceDeskApprovalStatus, enum_values
from app.modules.access.models import ServiceDeskUser
from app.modules.templates.models import ServiceDeskTemplateVersion

if TYPE_CHECKING:
    from app.modules.tickets.models import ServiceDeskTicket


class ServiceDeskApprovalWorkflow(Base):
    __tablename__ = "service_desk_approval_workflows"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_template_versions.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    template_version: Mapped[ServiceDeskTemplateVersion] = relationship()
    stages: Mapped[list["ServiceDeskApprovalStage"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="ServiceDeskApprovalStage.position",
    )


class ServiceDeskApprovalStage(Base):
    __tablename__ = "service_desk_approval_stages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_approval_workflows.id"),
        index=True,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    decision_rule: Mapped[ApprovalDecisionRule] = mapped_column(
        SAEnum(ApprovalDecisionRule, values_callable=enum_values, native_enum=False, length=16),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    workflow: Mapped[ServiceDeskApprovalWorkflow] = relationship(back_populates="stages")
    approvers: Mapped[list["ServiceDeskApprovalStageApprover"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by="ServiceDeskApprovalStageApprover.created_at",
    )


class ServiceDeskApprovalStageApprover(Base):
    __tablename__ = "service_desk_approval_stage_approvers"
    __table_args__ = (
        UniqueConstraint("stage_id", "service_desk_user_id", name="uq_sd_stage_approver_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_approval_stages.id"),
        index=True,
        nullable=False,
    )
    service_desk_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    stage: Mapped[ServiceDeskApprovalStage] = relationship(back_populates="approvers")
    user: Mapped[ServiceDeskUser] = relationship()


class ServiceDeskTicketApprovalStage(Base):
    __tablename__ = "service_desk_ticket_approval_stages"
    __table_args__ = (
        UniqueConstraint("ticket_id", "position", name="uq_sd_ticket_approval_stage_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_tickets.id"),
        index=True,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    decision_rule: Mapped[ApprovalDecisionRule] = mapped_column(
        SAEnum(ApprovalDecisionRule, values_callable=enum_values, native_enum=False, length=16),
        nullable=False,
    )
    status: Mapped[ServiceDeskApprovalStatus] = mapped_column(
        SAEnum(ServiceDeskApprovalStatus, values_callable=enum_values, native_enum=False, length=16),
        nullable=False,
        default=ServiceDeskApprovalStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    ticket: Mapped["ServiceDeskTicket"] = relationship(back_populates="approval_stages")
    approvals: Mapped[list["ServiceDeskTicketApproval"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by="ServiceDeskTicketApproval.created_at",
    )


class ServiceDeskTicketApproval(Base):
    __tablename__ = "service_desk_ticket_approvals"
    __table_args__ = (
        UniqueConstraint("ticket_approval_stage_id", "approver_user_id", name="uq_sd_ticket_approval_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_approval_stage_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_ticket_approval_stages.id"),
        index=True,
        nullable=False,
    )
    approver_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[ServiceDeskApprovalStatus] = mapped_column(
        SAEnum(ServiceDeskApprovalStatus, values_callable=enum_values, native_enum=False, length=16),
        nullable=False,
        default=ServiceDeskApprovalStatus.PENDING,
    )
    decision_comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    stage: Mapped[ServiceDeskTicketApprovalStage] = relationship(back_populates="approvals")
    approver: Mapped[ServiceDeskUser] = relationship()

    @property
    def approver_display_name(self) -> str:
        return self.approver.display_name
