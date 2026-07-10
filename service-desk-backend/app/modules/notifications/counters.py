from sqlalchemy import distinct, func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskApprovalStatus, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.access.service import ServiceDeskAccessService
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.tickets.models import ServiceDeskTicket


ACTIVE_ASSIGNEE_STATUSES = (
    ServiceDeskTicketStatus.ASSIGNED,
    ServiceDeskTicketStatus.IN_PROGRESS,
    ServiceDeskTicketStatus.WAITING_REQUESTER,
    ServiceDeskTicketStatus.WAITING_EXTERNAL,
)


class ServiceDeskCounterService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def for_actor(self, actor: ServiceDeskUser) -> dict[str, int | None]:
        capabilities = ServiceDeskAccessService.capabilities_for(actor)
        approvals = self.db.scalar(
            select(func.count(distinct(ServiceDeskTicket.id)))
            .join(ServiceDeskTicketApprovalStage, ServiceDeskTicketApprovalStage.ticket_id == ServiceDeskTicket.id)
            .join(ServiceDeskTicketApproval, ServiceDeskTicketApproval.ticket_approval_stage_id == ServiceDeskTicketApprovalStage.id)
            .where(
                ServiceDeskTicketApproval.approver_user_id == actor.id,
                ServiceDeskTicketApproval.status == ServiceDeskApprovalStatus.PENDING,
                ServiceDeskTicketApprovalStage.status == ServiceDeskApprovalStatus.PENDING,
                ServiceDeskTicketApprovalStage.started_at.is_not(None),
                ServiceDeskTicket.status == ServiceDeskTicketStatus.PENDING_APPROVAL,
                ServiceDeskTicket.deleted_at.is_(None),
            )
        ) or 0
        assigned = self._ticket_count(
            ServiceDeskTicket.assignee_user_id == actor.id,
            ServiceDeskTicket.status.in_(ACTIVE_ASSIGNEE_STATUSES),
        )
        awaiting_response = self._ticket_count(
            ServiceDeskTicket.requester_user_id == actor.id,
            ServiceDeskTicket.status == ServiceDeskTicketStatus.WAITING_REQUESTER,
        )
        sla_breaches = None
        if "service_desk.manage_sla" in capabilities:
            access_filter = True
            if "service_desk.view_all_tickets" not in capabilities:
                access_filter = or_(
                    ServiceDeskTicket.requester_user_id == actor.id,
                    ServiceDeskTicket.assignee_user_id == actor.id,
                )
            sla_breaches = self._ticket_count(
                access_filter,
                or_(
                    ServiceDeskTicket.is_response_breached.is_(True),
                    ServiceDeskTicket.is_resolution_breached.is_(True),
                ),
            )
        return {
            "waiting_my_approval": approvals,
            "assigned_to_me": assigned,
            "awaiting_my_response": awaiting_response,
            "sla_breaches": sla_breaches,
        }

    def _ticket_count(self, *filters) -> int:
        return self.db.scalar(select(func.count()).select_from(ServiceDeskTicket).where(
            ServiceDeskTicket.deleted_at.is_(None), *filters
        )) or 0
