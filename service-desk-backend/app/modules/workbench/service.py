import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import ServiceDeskAccessType, ServiceDeskPriority, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.access.service import ServiceDeskAccessService
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.catalog.models import ServiceDeskService
from app.modules.sla.models import ServiceDeskSlaEscalationEvent, ServiceDeskTicketSlaPause
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.tickets.policy import TicketPolicyService
from app.modules.workbench.schemas import (
    WorkbenchEntitySummary,
    WorkbenchSlaState,
    WorkbenchSlaSummary,
    WorkbenchTicketPage,
    WorkbenchTicketRow,
    WorkbenchUserSummary,
)


OPERATIONAL_CAPABILITIES = frozenset({
    "service_desk.be_assignee",
    "service_desk.approve",
    "service_desk.assign",
    "service_desk.change_priority",
    "service_desk.view_all_tickets",
})


class WorkbenchAccessService:
    @staticmethod
    def can_access(actor: ServiceDeskUser) -> bool:
        if actor.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            return True
        return bool(OPERATIONAL_CAPABILITIES & set(ServiceDeskAccessService.capabilities_for(actor)))

    def require_access(self, actor: ServiceDeskUser) -> None:
        if not self.can_access(actor):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к рабочему месту Service Desk")


def workbench_visibility(actor: ServiceDeskUser):
    capabilities = set(ServiceDeskAccessService.capabilities_for(actor))
    non_draft = ServiceDeskTicket.status != ServiceDeskTicketStatus.DRAFT
    own_draft = ServiceDeskTicket.requester_user_id == actor.id
    if "service_desk.view_all_tickets" in capabilities:
        return or_(non_draft, own_draft)
    approver_ticket = exists().where(
        ServiceDeskTicketApprovalStage.ticket_id == ServiceDeskTicket.id,
        ServiceDeskTicketApproval.ticket_approval_stage_id == ServiceDeskTicketApprovalStage.id,
        ServiceDeskTicketApproval.approver_user_id == actor.id,
    )
    return and_(
        or_(non_draft, own_draft),
        or_(
            ServiceDeskTicket.requester_user_id == actor.id,
            ServiceDeskTicket.assignee_user_id == actor.id,
            approver_ticket,
        ),
    )


def active_pause_predicate():
    return exists().where(
        ServiceDeskTicketSlaPause.ticket_id == ServiceDeskTicket.id,
        ServiceDeskTicketSlaPause.ended_at.is_(None),
    )


def objective_breach_predicate(now: datetime):
    response_due = and_(
        ServiceDeskTicket.first_response_at.is_(None),
        ServiceDeskTicket.first_response_due_at.is_not(None),
        ServiceDeskTicket.first_response_due_at < now,
    )
    resolution_due = and_(
        ServiceDeskTicket.resolved_at.is_(None),
        ServiceDeskTicket.resolution_due_at.is_not(None),
        ServiceDeskTicket.resolution_due_at < now,
    )
    return and_(~active_pause_predicate(), or_(response_due, resolution_due))


def sla_state_predicate(state: WorkbenchSlaState, now: datetime):
    has_sla = ServiceDeskTicket.sla_snapshot.is_not(None)
    paused = active_pause_predicate()
    breached = or_(
        ServiceDeskTicket.is_response_breached.is_(True),
        ServiceDeskTicket.is_resolution_breached.is_(True),
        objective_breach_predicate(now),
    )
    warned = exists().where(ServiceDeskSlaEscalationEvent.ticket_id == ServiceDeskTicket.id)
    if state == WorkbenchSlaState.NO_SLA:
        return ~has_sla
    if state == WorkbenchSlaState.PAUSED:
        return and_(has_sla, paused)
    if state == WorkbenchSlaState.BREACHED:
        return and_(has_sla, ~paused, breached)
    if state == WorkbenchSlaState.WARNING:
        return and_(has_sla, ~paused, ~breached, warned)
    return and_(has_sla, ~paused, ~breached, ~warned)


class WorkbenchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def tickets(
        self,
        actor: ServiceDeskUser,
        *,
        ticket_status: ServiceDeskTicketStatus | None,
        assignee_user_id: uuid.UUID | None,
        requester_user_id: uuid.UUID | None,
        priority: ServiceDeskPriority | None,
        category_id: uuid.UUID | None,
        service_id: uuid.UUID | None,
        sla_state: WorkbenchSlaState | None,
        overdue: bool | None,
        created_from: datetime | None,
        created_to: datetime | None,
        q: str | None,
        page: int,
        page_size: int,
    ) -> WorkbenchTicketPage:
        WorkbenchAccessService().require_access(actor)
        if created_from and created_to and created_from > created_to:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "created_from позже created_to")
        now = datetime.now(UTC)
        filters = [ServiceDeskTicket.deleted_at.is_(None), workbench_visibility(actor)]
        if ticket_status:
            filters.append(ServiceDeskTicket.status == ticket_status)
        if assignee_user_id:
            filters.append(ServiceDeskTicket.assignee_user_id == assignee_user_id)
        if requester_user_id:
            filters.append(ServiceDeskTicket.requester_user_id == requester_user_id)
        if priority:
            filters.append(ServiceDeskTicket.priority == priority)
        if category_id:
            filters.append(ServiceDeskService.category_id == category_id)
        if service_id:
            filters.append(ServiceDeskTicket.service_id == service_id)
        if sla_state:
            filters.append(sla_state_predicate(sla_state, now))
        if overdue is not None:
            predicate = objective_breach_predicate(now)
            filters.append(predicate if overdue else ~predicate)
        if created_from:
            filters.append(ServiceDeskTicket.created_at >= created_from)
        if created_to:
            filters.append(ServiceDeskTicket.created_at <= created_to)
        normalized_q = q.strip() if q else ""
        if normalized_q:
            pattern = f"%{normalized_q}%"
            filters.append(or_(
                ServiceDeskTicket.number.ilike(pattern),
                ServiceDeskTicket.title.ilike(pattern),
                ServiceDeskService.title.ilike(pattern),
            ))

        base: Select = select(ServiceDeskTicket.id).join(ServiceDeskTicket.service).where(*filters)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        ids = list(self.db.scalars(
            base.order_by(ServiceDeskTicket.updated_at.desc(), ServiceDeskTicket.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ))
        tickets: list[ServiceDeskTicket] = []
        if ids:
            tickets = list(self.db.scalars(
                select(ServiceDeskTicket)
                .options(
                    joinedload(ServiceDeskTicket.service).joinedload(ServiceDeskService.category),
                    joinedload(ServiceDeskTicket.requester),
                    joinedload(ServiceDeskTicket.assignee),
                    joinedload(ServiceDeskTicket.approval_stages).joinedload(
                        ServiceDeskTicketApprovalStage.approvals
                    ),
                )
                .where(ServiceDeskTicket.id.in_(ids))
                .order_by(ServiceDeskTicket.updated_at.desc(), ServiceDeskTicket.id.desc())
            ).unique())
        return WorkbenchTicketPage(
            items=[self._row(ticket, actor, now) for ticket in tickets],
            page=page,
            page_size=page_size,
            total=total,
            pages=(total + page_size - 1) // page_size,
        )

    def _row(self, ticket: ServiceDeskTicket, actor: ServiceDeskUser, now: datetime) -> WorkbenchTicketRow:
        return WorkbenchTicketRow(
            ticket_id=ticket.id,
            number=ticket.number,
            title=ticket.title,
            service=WorkbenchEntitySummary(id=ticket.service.id, title=ticket.service.title),
            category=WorkbenchEntitySummary(id=ticket.service.category.id, title=ticket.service.category.title),
            requester=WorkbenchUserSummary(id=ticket.requester.id, display_name=ticket.requester.display_name),
            assignee=(WorkbenchUserSummary(id=ticket.assignee.id, display_name=ticket.assignee.display_name) if ticket.assignee else None),
            priority=ticket.priority,
            status=ticket.status,
            sla=self._sla_summary(ticket, now),
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            allowed_actions=TicketPolicyService().allowed_actions(ticket, actor),
        )

    def _sla_summary(self, ticket: ServiceDeskTicket, now: datetime) -> WorkbenchSlaSummary:
        if not ticket.sla_snapshot:
            return WorkbenchSlaSummary(state=WorkbenchSlaState.NO_SLA)
        active_pause = self.db.scalar(select(ServiceDeskTicketSlaPause.id).where(
            ServiceDeskTicketSlaPause.ticket_id == ticket.id,
            ServiceDeskTicketSlaPause.ended_at.is_(None),
        ))
        metric = "first_response" if ticket.first_response_at is None else "resolution"
        due_at = ticket.first_response_due_at if metric == "first_response" else ticket.resolution_due_at
        if active_pause:
            state = WorkbenchSlaState.PAUSED
        elif ticket.is_response_breached or ticket.is_resolution_breached or (
            ticket.resolved_at is None
            and due_at is not None
            and due_at.replace(tzinfo=due_at.tzinfo or UTC) < now
        ):
            state = WorkbenchSlaState.BREACHED
        elif self.db.scalar(select(ServiceDeskSlaEscalationEvent.id).where(
            ServiceDeskSlaEscalationEvent.ticket_id == ticket.id
        )):
            state = WorkbenchSlaState.WARNING
        else:
            state = WorkbenchSlaState.ON_TRACK
        if ticket.resolved_at is not None:
            metric, due_at = None, None
        return WorkbenchSlaSummary(state=state, metric=metric, due_at=due_at)
