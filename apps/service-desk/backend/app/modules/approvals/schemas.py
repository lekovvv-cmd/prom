import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ApprovalDecisionRule, ApprovalMode, ServiceDeskApprovalStatus
from app.modules.templates.schemas import TemplateVersionRead


class ApprovalWorkflowConfigure(BaseModel):
    approval_mode: ApprovalMode
    name: str = Field(default="Согласование заявки", min_length=2, max_length=255)
    is_active: bool = True


class ApprovalWorkflowStageApply(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    decision_rule: ApprovalDecisionRule
    approver_user_ids: list[uuid.UUID] = Field(min_length=1)


class ApprovalWorkflowApply(BaseModel):
    approval_mode: ApprovalMode
    name: str = Field(default="Согласование заявки", min_length=2, max_length=255)
    stages: list[ApprovalWorkflowStageApply] = Field(default_factory=list)


class ApprovalStageCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    decision_rule: ApprovalDecisionRule
    position: int | None = Field(default=None, ge=0)


class ApprovalStageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    decision_rule: ApprovalDecisionRule | None = None
    position: int | None = Field(default=None, ge=0)


class ApprovalStagesReorder(BaseModel):
    stage_ids: list[uuid.UUID]


class ApprovalStageApproverCreate(BaseModel):
    service_desk_user_id: uuid.UUID


class ApprovalStageApproverRead(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    service_desk_user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalStageRead(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    position: int
    title: str
    decision_rule: ApprovalDecisionRule
    created_at: datetime
    updated_at: datetime
    approvers: list[ApprovalStageApproverRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ApprovalWorkflowRead(BaseModel):
    id: uuid.UUID
    template_version_id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    stages: list[ApprovalStageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ApprovalWorkflowConfigurationRead(BaseModel):
    template_version_id: uuid.UUID
    approval_mode: ApprovalMode
    workflow: ApprovalWorkflowRead | None


class ServiceApprovalWorkflowConfigurationRead(ApprovalWorkflowConfigurationRead):
    template_version: TemplateVersionRead


class TicketApprovalRead(BaseModel):
    id: uuid.UUID
    ticket_approval_stage_id: uuid.UUID
    approver_user_id: uuid.UUID
    approver_display_name: str
    status: ServiceDeskApprovalStatus
    decision_comment: str | None
    decided_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketApprovalStageRead(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    position: int
    title: str
    decision_rule: ApprovalDecisionRule
    status: ServiceDeskApprovalStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    approvals: list[TicketApprovalRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TicketApprovalDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class TicketApprovalRejection(BaseModel):
    comment: str = Field(min_length=2, max_length=2000)
