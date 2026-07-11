from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskApprovalStatus, ServiceDeskPriority, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.access.service import ServiceDeskAccessService
from app.modules.approvals.models import ServiceDeskTicketApprovalStage
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.stats.schemas import (
    ApprovalMetricsRead,
    AssigneeStatsRow,
    BacklogBucket,
    DistributionItem,
    DurationStats,
    SlaMetricsRead,
    StatsFilters,
    SummaryRead,
    TimeMetricsRead,
)
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.workbench.service import sla_state_predicate
from app.modules.workbench.schemas import WorkbenchSlaState

TERMINAL_STATUSES = (ServiceDeskTicketStatus.CLOSED, ServiceDeskTicketStatus.CANCELLED)
CURRENT_ASSIGNED = (
    ServiceDeskTicketStatus.ASSIGNED,
    ServiceDeskTicketStatus.IN_PROGRESS,
    ServiceDeskTicketStatus.WAITING_REQUESTER,
    ServiceDeskTicketStatus.WAITING_EXTERNAL,
    ServiceDeskTicketStatus.RESOLVED,
)


class StatsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def require_access(actor: ServiceDeskUser) -> None:
        if "service_desk.view_reports" not in ServiceDeskAccessService.capabilities_for(actor):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к отчётам Service Desk")

    def _dimension_filters(self, filters: StatsFilters):
        values = [ServiceDeskTicket.deleted_at.is_(None)]
        if filters.service_id:
            values.append(ServiceDeskTicket.service_id == filters.service_id)
        if filters.category_id:
            values.append(ServiceDeskService.category_id == filters.category_id)
        if filters.assignee_user_id:
            values.append(ServiceDeskTicket.assignee_user_id == filters.assignee_user_id)
        if filters.priority:
            values.append(ServiceDeskTicket.priority == filters.priority)
        return values

    def _period(self, column, filters: StatsFilters):
        start, end = filters.boundaries()
        values = []
        if start:
            values.append(column >= start)
        if end:
            values.append(column < end)
        return values

    def _count(self, filters: StatsFilters, *conditions) -> int:
        return (
            self.db.scalar(
                select(func.count(ServiceDeskTicket.id))
                .join(ServiceDeskTicket.service)
                .where(*self._dimension_filters(filters), *conditions)
            )
            or 0
        )

    def summary(self, actor: ServiceDeskUser, filters: StatsFilters) -> SummaryRead:
        self.require_access(actor)

        def current(value: ServiceDeskTicketStatus) -> int:
            return self._count(filters, ServiceDeskTicket.status == value)

        return SummaryRead(
            created=self._count(
                filters,
                ServiceDeskTicket.status != ServiceDeskTicketStatus.DRAFT,
                *self._period(ServiceDeskTicket.submitted_at, filters),
            ),
            closed_in_period=self._count(
                filters, *self._period(ServiceDeskTicket.closed_at, filters)
            ),
            current_backlog=self._count(
                filters,
                ServiceDeskTicket.submitted_at.is_not(None),
                ServiceDeskTicket.status.not_in(TERMINAL_STATUSES),
            ),
            submitted=current(ServiceDeskTicketStatus.SUBMITTED),
            pending_approval=current(ServiceDeskTicketStatus.PENDING_APPROVAL),
            approved_in_period=self._count(
                filters, *self._period(ServiceDeskTicket.approved_at, filters)
            ),
            rejected_in_period=self._count(
                filters, *self._period(ServiceDeskTicket.rejected_at, filters)
            ),
            assigned=current(ServiceDeskTicketStatus.ASSIGNED),
            in_progress=current(ServiceDeskTicketStatus.IN_PROGRESS),
            waiting_requester=current(ServiceDeskTicketStatus.WAITING_REQUESTER),
            waiting_external=current(ServiceDeskTicketStatus.WAITING_EXTERNAL),
            resolved=current(ServiceDeskTicketStatus.RESOLVED),
            closed=current(ServiceDeskTicketStatus.CLOSED),
            cancelled_in_period=self._count(
                filters, *self._period(ServiceDeskTicket.cancelled_at, filters)
            ),
            priorities=self._enum_distribution(
                filters, ServiceDeskTicket.priority, ServiceDeskPriority
            ),
        )

    def _enum_distribution(self, filters, column, enum_type):
        rows = dict(
            self.db.execute(
                select(column, func.count(ServiceDeskTicket.id))
                .join(ServiceDeskTicket.service)
                .where(
                    *self._dimension_filters(filters),
                    ServiceDeskTicket.status != ServiceDeskTicketStatus.DRAFT,
                    *self._period(ServiceDeskTicket.submitted_at, filters),
                )
                .group_by(column)
            ).all()
        )
        return [
            DistributionItem(id=item.value, label=item.value, count=rows.get(item, 0))
            for item in enum_type
        ]

    def statuses(self, actor, filters):
        self.require_access(actor)
        return self._enum_distribution(filters, ServiceDeskTicket.status, ServiceDeskTicketStatus)

    def entities(self, actor, filters, kind: str):
        self.require_access(actor)
        model, id_col, label_col = (
            (ServiceDeskService, ServiceDeskService.id, ServiceDeskService.title)
            if kind == "services"
            else (ServiceDeskCategory, ServiceDeskCategory.id, ServiceDeskCategory.title)
        )
        stmt = (
            select(id_col, label_col, func.count(ServiceDeskTicket.id))
            .select_from(ServiceDeskTicket)
            .join(ServiceDeskService)
        )
        if kind == "categories":
            stmt = stmt.join(ServiceDeskCategory)
        rows = self.db.execute(
            stmt.where(
                *self._dimension_filters(filters),
                ServiceDeskTicket.status != ServiceDeskTicketStatus.DRAFT,
                *self._period(ServiceDeskTicket.submitted_at, filters),
            )
            .group_by(id_col, label_col)
            .order_by(label_col)
        ).all()
        return [
            DistributionItem(id=str(row[0]), label=row[1] or "Удалённый объект", count=row[2])
            for row in rows
        ]

    @staticmethod
    def _duration(values: list[float]) -> DurationStats:
        values = sorted(max(0.0, value) for value in values)
        if not values:
            return DurationStats(
                average_seconds=None, median_seconds=None, p90_seconds=None, sample_size=0
            )

        def percentile(p: float):
            index = (len(values) - 1) * p
            lower = math.floor(index)
            upper = math.ceil(index)
            return (
                values[lower]
                if lower == upper
                else values[lower] + (values[upper] - values[lower]) * (index - lower)
            )

        return DurationStats(
            average_seconds=sum(values) / len(values),
            median_seconds=percentile(0.5),
            p90_seconds=percentile(0.9),
            sample_size=len(values),
        )

    def _duration_values(self, filters, start_col, end_col):
        rows = self.db.execute(
            select(start_col, end_col)
            .select_from(ServiceDeskTicket)
            .join(ServiceDeskTicket.service)
            .where(
                *self._dimension_filters(filters),
                start_col.is_not(None),
                end_col.is_not(None),
                *self._period(end_col, filters),
            )
        ).all()
        return [(end - start).total_seconds() for start, end in rows]

    def times(self, actor, filters):
        self.require_access(actor)
        # Assignment readiness is approval completion when present, otherwise submission.
        assignment_start = func.coalesce(
            ServiceDeskTicket.approved_at, ServiceDeskTicket.submitted_at
        )
        return TimeMetricsRead(
            time_to_approval=self._duration(
                self._duration_values(
                    filters, ServiceDeskTicket.submitted_at, ServiceDeskTicket.approved_at
                )
            ),
            time_to_assignment=self._duration(
                self._duration_values(filters, assignment_start, ServiceDeskTicket.assigned_at)
            ),
            first_response_time=self._duration(
                self._duration_values(
                    filters, ServiceDeskTicket.submitted_at, ServiceDeskTicket.first_response_at
                )
            ),
            resolution_time=self._duration(
                self._duration_values(
                    filters, ServiceDeskTicket.submitted_at, ServiceDeskTicket.resolved_at
                )
            ),
            close_after_resolution_time=self._duration(
                self._duration_values(
                    filters, ServiceDeskTicket.resolved_at, ServiceDeskTicket.closed_at
                )
            ),
        )

    def sla(self, actor, filters):
        self.require_access(actor)
        now = datetime.now(UTC)
        response_total = self._count(
            filters,
            ServiceDeskTicket.sla_snapshot.is_not(None),
            ServiceDeskTicket.first_response_at.is_not(None),
            *self._period(ServiceDeskTicket.first_response_at, filters),
        )
        resolution_total = self._count(
            filters,
            ServiceDeskTicket.sla_snapshot.is_not(None),
            ServiceDeskTicket.resolved_at.is_not(None),
            *self._period(ServiceDeskTicket.resolved_at, filters),
        )
        response_breached_cohort = self._count(
            filters,
            ServiceDeskTicket.sla_snapshot.is_not(None),
            ServiceDeskTicket.first_response_at.is_not(None),
            ServiceDeskTicket.is_response_breached.is_(True),
            *self._period(ServiceDeskTicket.first_response_at, filters),
        )
        resolution_breached_cohort = self._count(
            filters,
            ServiceDeskTicket.sla_snapshot.is_not(None),
            ServiceDeskTicket.resolved_at.is_not(None),
            ServiceDeskTicket.is_resolution_breached.is_(True),
            *self._period(ServiceDeskTicket.resolved_at, filters),
        )
        response_breach_events = self._count(
            filters,
            ServiceDeskTicket.response_breached_at.is_not(None),
            *self._period(ServiceDeskTicket.response_breached_at, filters),
        )
        resolution_breach_events = self._count(
            filters,
            ServiceDeskTicket.resolution_breached_at.is_not(None),
            *self._period(ServiceDeskTicket.resolution_breached_at, filters),
        )
        active = [
            ServiceDeskTicket.submitted_at.is_not(None),
            ServiceDeskTicket.status.not_in(TERMINAL_STATUSES),
        ]
        return SlaMetricsRead(
            response_compliance_percent=round((response_total - response_breached_cohort) * 100 / response_total, 2)
            if response_total
            else None,
            resolution_compliance_percent=round((resolution_total - resolution_breached_cohort) * 100 / resolution_total, 2)
            if resolution_total
            else None,
            response_breaches=response_breach_events,
            resolution_breaches=resolution_breach_events,
            active_near_breach=self._count(
                filters, *active, sla_state_predicate(WorkbenchSlaState.WARNING, now)
            ),
            active_breached=self._count(
                filters, *active, sla_state_predicate(WorkbenchSlaState.BREACHED, now)
            ),
        )

    def backlog(self, actor, filters):
        self.require_access(actor)
        now = datetime.now(UTC)
        specs = [
            ("0_1", "0–1 день", 0, 2),
            ("2_3", "2–3 дня", 2, 4),
            ("4_7", "4–7 дней", 4, 8),
            ("8_14", "8–14 дней", 8, 15),
            ("15_plus", "15+ дней", 15, None),
        ]
        result = []
        for code, label, low, high in specs:
            conditions = [
                ServiceDeskTicket.submitted_at.is_not(None),
                ServiceDeskTicket.status.not_in(TERMINAL_STATUSES),
                ServiceDeskTicket.submitted_at <= now - timedelta(days=low),
            ]
            if high is not None:
                conditions.append(ServiceDeskTicket.submitted_at > now - timedelta(days=high))
            result.append(
                BacklogBucket(code=code, label=label, count=self._count(filters, *conditions))
            )
        return result

    def assignees(self, actor, filters):
        self.require_access(actor)
        users = self.db.scalars(
            select(ServiceDeskUser)
            .where(exists().where(ServiceDeskTicket.assignee_user_id == ServiceDeskUser.id))
            .order_by(ServiceDeskUser.display_name, ServiceDeskUser.id)
        ).all()
        if not users:
            return []
        user_ids = [user.id for user in users]
        base_filters = [
            *self._dimension_filters(filters),
            ServiceDeskTicket.assignee_user_id.in_(user_ids),
        ]
        current_rows = self.db.execute(
            select(
                ServiceDeskTicket.assignee_user_id,
                func.sum(case((ServiceDeskTicket.status.in_(CURRENT_ASSIGNED), 1), else_=0)),
                func.sum(case((ServiceDeskTicket.status == ServiceDeskTicketStatus.IN_PROGRESS, 1), else_=0)),
                func.sum(case((
                    ServiceDeskTicket.status.in_((
                        ServiceDeskTicketStatus.WAITING_REQUESTER,
                        ServiceDeskTicketStatus.WAITING_EXTERNAL,
                    )),
                    1,
                ), else_=0)),
                func.sum(case((or_(
                    ServiceDeskTicket.response_breached_at.is_not(None),
                    ServiceDeskTicket.resolution_breached_at.is_not(None),
                ), 1), else_=0)),
            )
            .join(ServiceDeskTicket.service)
            .where(*base_filters)
            .group_by(ServiceDeskTicket.assignee_user_id)
        ).all()
        current_by_user = {row[0]: row[1:] for row in current_rows}
        outcome_rows = self.db.execute(
            select(
                ServiceDeskTicket.assignee_user_id,
                func.sum(case((
                    and_(
                        ServiceDeskTicket.resolved_at.is_not(None),
                        *self._period(ServiceDeskTicket.resolved_at, filters),
                    ),
                    1,
                ), else_=0)),
                func.sum(case((
                    and_(
                        ServiceDeskTicket.closed_at.is_not(None),
                        *self._period(ServiceDeskTicket.closed_at, filters),
                    ),
                    1,
                ), else_=0)),
            )
            .join(ServiceDeskTicket.service)
            .where(*base_filters)
            .group_by(ServiceDeskTicket.assignee_user_id)
        ).all()
        outcomes_by_user = {row[0]: row[1:] for row in outcome_rows}
        duration_rows = self.db.execute(
            select(
                ServiceDeskTicket.assignee_user_id,
                ServiceDeskTicket.submitted_at,
                ServiceDeskTicket.resolved_at,
            )
            .join(ServiceDeskTicket.service)
            .where(
                *base_filters,
                ServiceDeskTicket.submitted_at.is_not(None),
                ServiceDeskTicket.resolved_at.is_not(None),
                *self._period(ServiceDeskTicket.resolved_at, filters),
            )
        ).all()
        durations_by_user: dict[object, list[float]] = {user_id: [] for user_id in user_ids}
        for user_id, submitted_at, resolved_at in duration_rows:
            durations_by_user.setdefault(user_id, []).append(
                (resolved_at - submitted_at).total_seconds()
            )
        rows = []
        for user in users:
            current = current_by_user.get(user.id, (0, 0, 0, 0))
            outcomes = outcomes_by_user.get(user.id, (0, 0))
            rows.append(
                AssigneeStatsRow(
                    user_id=user.id,
                    display_name=user.display_name,
                    is_active=user.is_active,
                    currently_assigned=current[0] or 0,
                    in_progress=current[1] or 0,
                    waiting=current[2] or 0,
                    resolved_in_period=outcomes[0] or 0,
                    closed_in_period=outcomes[1] or 0,
                    breached_tickets=current[3] or 0,
                    median_resolution_seconds=self._duration(
                        durations_by_user.get(user.id, [])
                    ).median_seconds,
                )
            )
        return rows

    def approvals(self, actor, filters):
        self.require_access(actor)
        dims = self._dimension_filters(filters)
        base = (
            select(ServiceDeskTicketApprovalStage)
            .join(ServiceDeskTicket)
            .join(ServiceDeskTicket.service)
            .where(*dims)
        )
        pending = (
            self.db.scalar(
                select(func.count()).select_from(
                    base.where(
                        ServiceDeskTicketApprovalStage.status == ServiceDeskApprovalStatus.PENDING,
                        ServiceDeskTicketApprovalStage.started_at.is_not(None),
                    ).subquery()
                )
            )
            or 0
        )
        completed = self.db.execute(
            select(
                ServiceDeskTicketApprovalStage.started_at,
                ServiceDeskTicketApprovalStage.completed_at,
                ServiceDeskTicketApprovalStage.status,
            )
            .join(ServiceDeskTicket)
            .join(ServiceDeskTicket.service)
            .where(
                *dims,
                ServiceDeskTicketApprovalStage.started_at.is_not(None),
                ServiceDeskTicketApprovalStage.completed_at.is_not(None),
                *self._period(ServiceDeskTicketApprovalStage.completed_at, filters),
            )
        ).all()
        duration = self._duration([(end - start).total_seconds() for start, end, _ in completed])
        rejected = sum(
            1 for _, _, state in completed if state == ServiceDeskApprovalStatus.REJECTED
        )
        return ApprovalMetricsRead(
            pending_approval_stages=pending,
            stage_duration=duration,
            rejection_rate_percent=round(rejected * 100 / len(completed), 2) if completed else None,
        )
