import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import (
    ApprovalMode,
    ServiceDeskApprovalStatus,
    ServiceDeskTicketAction,
)
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.approvals.repository import ApprovalWorkflowRepository
from app.modules.approvals.service import ApprovalWorkflowService
from app.modules.templates.models import ServiceDeskTemplateVersion
from app.modules.tickets.lifecycle import TicketLifecycleService
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.tickets.repository import TicketRepository


class TicketApprovalService:
    def __init__(self, db: Session, ticket_repository: TicketRepository) -> None:
        self.db = db
        self.repository = ApprovalWorkflowRepository(db)
        self.workflow_service = ApprovalWorkflowService(db)
        self.ticket_repository = ticket_repository
        self.lifecycle = TicketLifecycleService(ticket_repository)

    def initialize_snapshot(
        self,
        ticket: ServiceDeskTicket,
        template_version: ServiceDeskTemplateVersion,
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        if self.repository.list_ticket_stages(ticket.id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Workflow заявки уже создан")

        now = occurred_at or datetime.now(UTC)
        if template_version.approval_mode == ApprovalMode.NONE:
            self.lifecycle.perform_transition(
                ticket,
                ServiceDeskTicketAction.SKIP_APPROVAL,
                actor=None,
                occurred_at=now,
            )
            return

        self.workflow_service.validate_for_publish(template_version)
        workflow = self.repository.get_workflow_by_version(template_version.id)
        if workflow is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Workflow согласования не найден")

        for index, source_stage in enumerate(sorted(workflow.stages, key=lambda stage: stage.position)):
            ticket_stage = self.repository.add_ticket_stage(
                ServiceDeskTicketApprovalStage(
                    ticket_id=ticket.id,
                    position=index,
                    title=source_stage.title,
                    decision_rule=source_stage.decision_rule,
                    status=ServiceDeskApprovalStatus.PENDING,
                    started_at=now if index == 0 else None,
                )
            )
            for source_approver in source_stage.approvers:
                self.repository.add_ticket_approval(
                    ServiceDeskTicketApproval(
                        ticket_approval_stage_id=ticket_stage.id,
                        approver_user_id=source_approver.service_desk_user_id,
                        status=ServiceDeskApprovalStatus.PENDING,
                    )
                )

        self.lifecycle.perform_transition(
            ticket,
            ServiceDeskTicketAction.START_APPROVAL,
            actor=None,
            occurred_at=now,
        )

    def get_snapshot(self, ticket_id: uuid.UUID) -> list[ServiceDeskTicketApprovalStage]:
        if not self.ticket_repository.get_ticket(ticket_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return self.repository.list_ticket_stages(ticket_id)
