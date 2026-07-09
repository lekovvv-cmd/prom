import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ApprovalDecisionRule, ApprovalMode


class ApprovalWorkflowConfigure(BaseModel):
    approval_mode: ApprovalMode
    name: str = Field(default="Согласование заявки", min_length=2, max_length=255)
    is_active: bool = True


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
