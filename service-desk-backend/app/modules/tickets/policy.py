from fastapi import HTTPException, status

from app.core.enums import ServiceDeskAccessType, ServiceDeskApprovalStatus, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.access.service import ServiceDeskAccessService
from app.modules.tickets.models import ServiceDeskTicket


class TicketPolicyService:
    def can_view(self, ticket: ServiceDeskTicket, actor: ServiceDeskUser) -> bool:
        capabilities = set(ServiceDeskAccessService.capabilities_for(actor))
        if "service_desk.view_all_tickets" in capabilities:
            return True
        if actor.id in {ticket.requester_user_id, ticket.assignee_user_id}:
            return True
        return any(
            approval.approver_user_id == actor.id
            for stage in ticket.approval_stages
            for approval in stage.approvals
        )

    def require_view(self, ticket: ServiceDeskTicket, actor: ServiceDeskUser) -> None:
        if not self.can_view(ticket, actor):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к заявке")

    def can_view_internal_comments(self, ticket: ServiceDeskTicket, actor: ServiceDeskUser) -> bool:
        if actor.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            return True
        if actor.id == ticket.assignee_user_id:
            return True
        capabilities = set(ServiceDeskAccessService.capabilities_for(actor))
        return "service_desk.view_all_tickets" in capabilities

    def require_internal_comments(self, ticket: ServiceDeskTicket, actor: ServiceDeskUser) -> None:
        if not self.can_view_internal_comments(ticket, actor):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к внутренним комментариям")

    def allowed_actions(self, ticket: ServiceDeskTicket, actor: ServiceDeskUser) -> list[str]:
        capabilities = set(ServiceDeskAccessService.capabilities_for(actor))
        actions: list[str] = []
        if "service_desk.assign" in capabilities:
            if ticket.status == ServiceDeskTicketStatus.APPROVED:
                actions.append("assign")
            elif ticket.status in {
                ServiceDeskTicketStatus.ASSIGNED,
                ServiceDeskTicketStatus.IN_PROGRESS,
                ServiceDeskTicketStatus.WAITING_REQUESTER,
                ServiceDeskTicketStatus.WAITING_EXTERNAL,
            }:
                actions.append("reassign")
        if (
            ticket.status != ServiceDeskTicketStatus.PENDING_APPROVAL
            or "service_desk.approve" not in capabilities
        ):
            return actions

        has_active_approval = any(
            stage.status == ServiceDeskApprovalStatus.PENDING
            and stage.started_at is not None
            and approval.approver_user_id == actor.id
            and approval.status == ServiceDeskApprovalStatus.PENDING
            for stage in ticket.approval_stages
            for approval in stage.approvals
        )
        return [*actions, "approve", "reject"] if has_active_approval else actions
