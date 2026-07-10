import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import (
    ApprovalDecisionRule,
    ApprovalMode,
    ServiceDeskAccessType,
    ServiceDeskApprovalStatus,
    ServiceDeskTicketAction,
    ServiceDeskTicketStatus,
)
from app.modules.access.models import ServiceDeskUser
from app.modules.assignments.policy import AssigneePolicy
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.approvals.repository import ApprovalWorkflowRepository
from app.modules.approvals.service import ApprovalWorkflowService
from app.modules.templates.models import ServiceDeskTemplateVersion
from app.modules.tickets.lifecycle import TicketLifecycleService
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.repository import TicketRepository


@dataclass
class _DecisionContext:
    ticket: ServiceDeskTicket
    stage: ServiceDeskTicketApprovalStage
    approval: ServiceDeskTicketApproval
    stage_approvals: list[ServiceDeskTicketApproval]
    actor: ServiceDeskUser


class TicketApprovalService:
    def __init__(self, db: Session, ticket_repository: TicketRepository) -> None:
        self.db = db
        self.repository = ApprovalWorkflowRepository(db)
        self.workflow_service = ApprovalWorkflowService(db)
        self.ticket_repository = ticket_repository
        self.lifecycle = TicketLifecycleService(ticket_repository)
        self.assignee_policy = AssigneePolicy(db)

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
            self._apply_default_assignment(ticket, template_version, now)
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

    def approve(
        self,
        ticket_id: uuid.UUID,
        approval_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        *,
        comment: str | None = None,
    ) -> ServiceDeskTicket:
        context = self._decision_context(ticket_id, approval_id, actor_user_id)
        now = datetime.now(UTC)
        context.approval.status = ServiceDeskApprovalStatus.APPROVED
        context.approval.decision_comment = comment.strip() if comment and comment.strip() else None
        context.approval.decided_at = now
        self._write_approval_history(context, "approval_approved", "Согласование одобрено")

        stage_is_complete = context.stage.decision_rule == ApprovalDecisionRule.ANY or all(
            approval.status == ServiceDeskApprovalStatus.APPROVED
            for approval in context.stage_approvals
        )
        if stage_is_complete:
            if context.stage.decision_rule == ApprovalDecisionRule.ANY:
                self._skip_pending_approvals(context.stage_approvals, now)
            context.stage.status = ServiceDeskApprovalStatus.APPROVED
            context.stage.completed_at = now
            self._advance_or_complete(context, now)

        self.db.commit()
        return self._require_ticket(ticket_id)

    def reject(
        self,
        ticket_id: uuid.UUID,
        approval_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        *,
        comment: str,
    ) -> ServiceDeskTicket:
        context = self._decision_context(ticket_id, approval_id, actor_user_id)
        now = datetime.now(UTC)
        normalized_comment = comment.strip()
        if not normalized_comment:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Укажите причину отклонения")

        context.approval.status = ServiceDeskApprovalStatus.REJECTED
        context.approval.decision_comment = normalized_comment
        context.approval.decided_at = now
        self._skip_pending_approvals(context.stage_approvals, now)
        context.stage.status = ServiceDeskApprovalStatus.REJECTED
        context.stage.completed_at = now

        later_stages = self.repository.list_later_stages_for_update(
            context.ticket.id,
            context.stage.position,
        )
        for later_stage in later_stages:
            later_stage.status = ServiceDeskApprovalStatus.SKIPPED
            later_stage.completed_at = now
            later_approvals = self.repository.list_stage_approvals_for_update(later_stage.id)
            self._skip_pending_approvals(later_approvals, now)

        self.lifecycle.perform_transition(
            context.ticket,
            ServiceDeskTicketAction.REJECT_APPROVAL,
            actor=context.actor,
            metadata={
                "approval_id": str(context.approval.id),
                "stage_id": str(context.stage.id),
                "stage_title": context.stage.title,
                "comment": normalized_comment,
            },
            occurred_at=now,
        )
        self.db.commit()
        return self._require_ticket(ticket_id)

    def _decision_context(
        self,
        ticket_id: uuid.UUID,
        approval_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> _DecisionContext:
        ids = self.repository.get_ticket_approval_context_ids(approval_id)
        if ids is None or ids[1] != ticket_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Решение согласования не найдено")
        stage_id, _ = ids

        ticket = self.ticket_repository.get_ticket_for_update(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        stage = self.repository.get_ticket_stage_for_update(stage_id)
        if not stage:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Этап согласования не найден")
        stage_approvals = self.repository.list_stage_approvals_for_update(stage.id)
        approval = next((item for item in stage_approvals if item.id == approval_id), None)
        if approval is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Решение согласования не найдено")

        actor = self.db.get(ServiceDeskUser, actor_user_id)
        if not actor or not actor.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к Service Desk")
        if actor.id != approval.approver_user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Решение доступно только назначенному согласующему")
        if not self._can_approve(actor):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет capability service_desk.approve")
        if ticket.status != ServiceDeskTicketStatus.PENDING_APPROVAL:
            raise HTTPException(status.HTTP_409_CONFLICT, "Заявка больше не находится на согласовании")
        if stage.status != ServiceDeskApprovalStatus.PENDING or stage.started_at is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Этап согласования ещё не активен")
        if approval.status != ServiceDeskApprovalStatus.PENDING:
            raise HTTPException(status.HTTP_409_CONFLICT, "Решение уже принято")

        return _DecisionContext(
            ticket=ticket,
            stage=stage,
            approval=approval,
            stage_approvals=stage_approvals,
            actor=actor,
        )

    def _advance_or_complete(self, context: _DecisionContext, now: datetime) -> None:
        later_stages = self.repository.list_later_stages_for_update(
            context.ticket.id,
            context.stage.position,
        )
        if later_stages:
            next_stage = later_stages[0]
            next_stage.started_at = now
            self.ticket_repository.add_history(
                ServiceDeskTicketHistory(
                    ticket_id=context.ticket.id,
                    event_type="approval_stage_started",
                    actor_user_id=context.actor.id,
                    message=f"Начат этап согласования «{next_stage.title}»",
                    payload={
                        "stage_id": str(next_stage.id),
                        "stage_title": next_stage.title,
                        "position": next_stage.position,
                    },
                )
            )
            return

        self.lifecycle.perform_transition(
            context.ticket,
            ServiceDeskTicketAction.COMPLETE_APPROVAL,
            actor=None,
            occurred_at=now,
        )
        template_version = self.db.get(ServiceDeskTemplateVersion, context.ticket.template_version_id)
        if not template_version:
            raise HTTPException(status.HTTP_409_CONFLICT, "Шаблон заявки не найден")
        self._apply_default_assignment(context.ticket, template_version, now)

    def _apply_default_assignment(
        self,
        ticket: ServiceDeskTicket,
        template_version: ServiceDeskTemplateVersion,
        now: datetime,
    ) -> None:
        default_assignee_user_id = (
            template_version.default_assignee_user_id
            or template_version.service.default_assignee_user_id
        )
        if not default_assignee_user_id:
            return

        assignee = self.assignee_policy.get_eligible_assignee(default_assignee_user_id)
        if not assignee:
            self.ticket_repository.add_history(
                ServiceDeskTicketHistory(
                    ticket_id=ticket.id,
                    event_type="default_assignment_skipped",
                    actor_user_id=None,
                    message="Исполнитель по умолчанию недоступен",
                    payload={
                        "default_assignee_user_id": str(default_assignee_user_id),
                        "assignment_source": "default",
                    },
                )
            )
            return

        self.lifecycle.perform_transition(
            ticket,
            ServiceDeskTicketAction.ASSIGN,
            actor=None,
            metadata={
                "assignee_user_id": str(assignee.id),
                "assignment_source": "default",
            },
            occurred_at=now,
        )

    def _write_approval_history(
        self,
        context: _DecisionContext,
        event_type: str,
        message: str,
    ) -> None:
        self.ticket_repository.add_history(
            ServiceDeskTicketHistory(
                ticket_id=context.ticket.id,
                event_type=event_type,
                actor_user_id=context.actor.id,
                message=message,
                payload={
                    "approval_id": str(context.approval.id),
                    "stage_id": str(context.stage.id),
                    "stage_title": context.stage.title,
                    "decision_rule": context.stage.decision_rule.value,
                    "comment": context.approval.decision_comment,
                },
            )
        )

    def _require_ticket(self, ticket_id: uuid.UUID) -> ServiceDeskTicket:
        ticket = self.ticket_repository.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
        return ticket

    @staticmethod
    def _skip_pending_approvals(
        approvals: list[ServiceDeskTicketApproval],
        now: datetime,
    ) -> None:
        for approval in approvals:
            if approval.status == ServiceDeskApprovalStatus.PENDING:
                approval.status = ServiceDeskApprovalStatus.SKIPPED
                approval.decided_at = now

    @staticmethod
    def _can_approve(user: ServiceDeskUser) -> bool:
        return user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN or any(
            capability.capability == "service_desk.approve" for capability in user.capabilities
        )
