import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.approvals.models import (
    ServiceDeskApprovalStage,
    ServiceDeskApprovalStageApprover,
    ServiceDeskApprovalWorkflow,
)


class ApprovalWorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_workflow_by_version(
        self,
        template_version_id: uuid.UUID,
    ) -> ServiceDeskApprovalWorkflow | None:
        stmt = (
            select(ServiceDeskApprovalWorkflow)
            .options(
                joinedload(ServiceDeskApprovalWorkflow.stages)
                .joinedload(ServiceDeskApprovalStage.approvers)
                .joinedload(ServiceDeskApprovalStageApprover.user)
            )
            .where(ServiceDeskApprovalWorkflow.template_version_id == template_version_id)
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def get_workflow(self, workflow_id: uuid.UUID) -> ServiceDeskApprovalWorkflow | None:
        stmt = (
            select(ServiceDeskApprovalWorkflow)
            .options(joinedload(ServiceDeskApprovalWorkflow.stages))
            .where(ServiceDeskApprovalWorkflow.id == workflow_id)
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def add_workflow(self, workflow: ServiceDeskApprovalWorkflow) -> ServiceDeskApprovalWorkflow:
        self.db.add(workflow)
        self.db.flush()
        return workflow

    def get_stage(self, stage_id: uuid.UUID) -> ServiceDeskApprovalStage | None:
        stmt = (
            select(ServiceDeskApprovalStage)
            .options(joinedload(ServiceDeskApprovalStage.approvers))
            .where(ServiceDeskApprovalStage.id == stage_id)
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def add_stage(self, stage: ServiceDeskApprovalStage) -> ServiceDeskApprovalStage:
        self.db.add(stage)
        self.db.flush()
        return stage

    def get_approver(self, approver_id: uuid.UUID) -> ServiceDeskApprovalStageApprover | None:
        return self.db.get(ServiceDeskApprovalStageApprover, approver_id)

    def get_stage_approver(
        self,
        stage_id: uuid.UUID,
        service_desk_user_id: uuid.UUID,
    ) -> ServiceDeskApprovalStageApprover | None:
        stmt = select(ServiceDeskApprovalStageApprover).where(
            ServiceDeskApprovalStageApprover.stage_id == stage_id,
            ServiceDeskApprovalStageApprover.service_desk_user_id == service_desk_user_id,
        )
        return self.db.scalar(stmt)

    def add_approver(
        self,
        approver: ServiceDeskApprovalStageApprover,
    ) -> ServiceDeskApprovalStageApprover:
        self.db.add(approver)
        self.db.flush()
        return approver
