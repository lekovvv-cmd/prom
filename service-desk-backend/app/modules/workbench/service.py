import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import ServiceDeskAccessType, ServiceDeskPriority, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.access.service import ServiceDeskAccessService
from app.modules.approvals.models import ServiceDeskTicketApproval, ServiceDeskTicketApprovalStage
from app.modules.catalog.models import ServiceDeskService
from app.modules.sla.models import ServiceDeskSlaEscalationEvent, ServiceDeskTicketSlaPause
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.tickets.policy import TicketPolicyService
from app.modules.workbench.schemas import (
    WorkbenchEntitySummary,
    WorkbenchCounters,
    WorkbenchQuickView,
    WorkbenchSlaState,
    WorkbenchSlaSummary,
    WorkbenchTicketPage,
    WorkbenchTicketRow,
    WorkbenchUserSummary,
    WorkbenchUserOption,
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
        quick_view: WorkbenchQuickView | None,
        page: int,
        page_size: int,
    ) -> WorkbenchTicketPage:
        WorkbenchAccessService().require_access(actor)
        if created_from and created_to and created_from > created_to:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "created_from позже created_to")
        now = datetime.now(UTC)
        filters = [ServiceDeskTicket.deleted_at.is_(None), workbench_visibility(actor)]
        if quick_view:
            filters.append(self.quick_view_predicate(quick_view, actor, now))
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
        paused_ids = set(self.db.scalars(select(ServiceDeskTicketSlaPause.ticket_id).where(
            ServiceDeskTicketSlaPause.ticket_id.in_(ids),
            ServiceDeskTicketSlaPause.ended_at.is_(None),
        ))) if ids else set()
        warned_ids = set(self.db.scalars(select(ServiceDeskSlaEscalationEvent.ticket_id).where(
            ServiceDeskSlaEscalationEvent.ticket_id.in_(ids),
        ))) if ids else set()
        return WorkbenchTicketPage(
            items=[self._row(ticket, actor, now, paused_ids, warned_ids) for ticket in tickets],
            page=page,
            page_size=page_size,
            total=total,
            pages=(total + page_size - 1) // page_size,
        )

    def counters(self, actor: ServiceDeskUser) -> WorkbenchCounters:
        WorkbenchAccessService().require_access(actor)
        now = datetime.now(UTC)
        base_filters = [ServiceDeskTicket.deleted_at.is_(None), workbench_visibility(actor)]
        capabilities = set(ServiceDeskAccessService.capabilities_for(actor))
        values: dict[str, int | None] = {}
        for quick_view in WorkbenchQuickView:
            if (
                quick_view == WorkbenchQuickView.SLA_BREACHED
                and "service_desk.manage_sla" not in capabilities
            ):
                values[quick_view.value] = None
                continue
            values[quick_view.value] = self.db.scalar(
                select(func.count()).select_from(ServiceDeskTicket).where(
                    *base_filters, self.quick_view_predicate(quick_view, actor, now)
                )
            ) or 0
        return WorkbenchCounters(**values)

    def user_options(
        self, actor: ServiceDeskUser, *, eligible_assignees: bool
    ) -> list[WorkbenchUserOption]:
        WorkbenchAccessService().require_access(actor)
        stmt = select(ServiceDeskUser).where(ServiceDeskUser.is_active.is_(True))
        if eligible_assignees:
            stmt = stmt.where(or_(
                ServiceDeskUser.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN,
                exists().where(
                    ServiceDeskUserCapability.service_desk_user_id == ServiceDeskUser.id,
                    ServiceDeskUserCapability.capability == "service_desk.be_assignee",
                ),
            ))
        users = self.db.scalars(stmt.order_by(ServiceDeskUser.display_name, ServiceDeskUser.id)).all()
        return [WorkbenchUserOption(id=user.id, display_name=user.display_name) for user in users]

    @staticmethod
    def quick_view_predicate(
        quick_view: WorkbenchQuickView, actor: ServiceDeskUser, now: datetime
    ):
        if quick_view == WorkbenchQuickView.WAITING_APPROVAL:
            return and_(
                ServiceDeskTicket.status == ServiceDeskTicketStatus.PENDING_APPROVAL,
                exists().where(
                    ServiceDeskTicketApprovalStage.ticket_id == ServiceDeskTicket.id,
                    ServiceDeskTicketApprovalStage.status == "pending",
                    ServiceDeskTicketApprovalStage.started_at.is_not(None),
                    ServiceDeskTicketApproval.ticket_approval_stage_id
                    == ServiceDeskTicketApprovalStage.id,
                    ServiceDeskTicketApproval.approver_user_id == actor.id,
                    ServiceDeskTicketApproval.status == "pending",
                ),
            )
        if quick_view == WorkbenchQuickView.ASSIGNED_TO_ME:
            return and_(
                ServiceDeskTicket.assignee_user_id == actor.id,
                ServiceDeskTicket.status.in_((
                    ServiceDeskTicketStatus.ASSIGNED,
                    ServiceDeskTicketStatus.IN_PROGRESS,
                    ServiceDeskTicketStatus.WAITING_REQUESTER,
                    ServiceDeskTicketStatus.WAITING_EXTERNAL,
                )),
            )
        status_by_view = {
            WorkbenchQuickView.IN_PROGRESS: ServiceDeskTicketStatus.IN_PROGRESS,
            WorkbenchQuickView.WAITING_REQUESTER: ServiceDeskTicketStatus.WAITING_REQUESTER,
            WorkbenchQuickView.WAITING_EXTERNAL: ServiceDeskTicketStatus.WAITING_EXTERNAL,
            WorkbenchQuickView.RESOLVED: ServiceDeskTicketStatus.RESOLVED,
        }
        if quick_view in status_by_view:
            return ServiceDeskTicket.status == status_by_view[quick_view]
        return sla_state_predicate(WorkbenchSlaState.BREACHED, now)

    def _row(
        self,
        ticket: ServiceDeskTicket,
        actor: ServiceDeskUser,
        now: datetime,
        paused_ids: set[uuid.UUID],
        warned_ids: set[uuid.UUID],
    ) -> WorkbenchTicketRow:
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
            sla=self._sla_summary(
                ticket, now, ticket.id in paused_ids, ticket.id in warned_ids
            ),
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            allowed_actions=TicketPolicyService().allowed_actions(ticket, actor),
            active_approval_id=self._active_approval_id(ticket, actor),
        )

    @staticmethod
    def _active_approval_id(ticket: ServiceDeskTicket, actor: ServiceDeskUser):
        for stage in ticket.approval_stages:
            if stage.status.value != "pending" or stage.started_at is None:
                continue
            for approval in stage.approvals:
                if approval.approver_user_id == actor.id and approval.status.value == "pending":
                    return approval.id
        return None

    @staticmethod
    def _sla_summary(
        ticket: ServiceDeskTicket,
        now: datetime,
        is_paused: bool,
        is_warned: bool,
    ) -> WorkbenchSlaSummary:
        if not ticket.sla_snapshot:
            return WorkbenchSlaSummary(state=WorkbenchSlaState.NO_SLA)
        metric = "first_response" if ticket.first_response_at is None else "resolution"
        due_at = ticket.first_response_due_at if metric == "first_response" else ticket.resolution_due_at
        if is_paused:
            state = WorkbenchSlaState.PAUSED
        elif ticket.is_response_breached or ticket.is_resolution_breached or (
            ticket.resolved_at is None
            and due_at is not None
            and due_at.replace(tzinfo=due_at.tzinfo or UTC) < now
        ):
            state = WorkbenchSlaState.BREACHED
        elif is_warned:
            state = WorkbenchSlaState.WARNING
        else:
            state = WorkbenchSlaState.ON_TRACK
        if ticket.resolved_at is not None:
            metric, due_at = None, None
        return WorkbenchSlaSummary(state=state, metric=metric, due_at=due_at)
