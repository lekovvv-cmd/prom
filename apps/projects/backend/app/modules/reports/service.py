from uuid import UUID

from platform_sdk.error_types import EntityNotFound, InvalidRequest, PermissionDenied
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork
from sqlalchemy.orm import Session

from app.core.enums import ReportPeriodStatus
from app.core.permissions import is_platform_admin
from app.modules.platform.events import ProjectEventRecorder
from app.modules.reports.repository import ReportRepository
from app.modules.reports.schemas import (
    AdminHalfYearReportRead,
    CurrentReportState,
    HalfYearReportPayload,
    HalfYearReportRead,
    ReportPeriodCreate,
    ReportPeriodRead,
)
from app.modules.users.models import User


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReportRepository(db)
        self.events = ProjectEventRecorder(db)

    def list_periods(self) -> list[ReportPeriodRead]:
        return [ReportPeriodRead.model_validate(period) for period in self.repo.list_periods()]

    def open_period(self, payload: ReportPeriodCreate, current_user: User) -> ReportPeriodRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._open_period(payload, current_user)
            uow.commit()
            return result

    def _open_period(self, payload: ReportPeriodCreate, current_user: User) -> ReportPeriodRead:
        self.repo.close_open_periods()
        period = self.repo.create_period(payload, current_user.id)
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.report_period_opened",
            object_type="report_period",
            object_id=period.id,
            after={"status": period.status.value, "title": period.title},
        )
        return ReportPeriodRead.model_validate(period)

    def close_period(self, period_id: UUID, current_user: User) -> ReportPeriodRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._close_period(period_id, current_user)
            uow.commit()
            return result

    def _close_period(self, period_id: UUID, current_user: User) -> ReportPeriodRead:
        period = self.repo.get_period(period_id)
        if period is None:
            raise EntityNotFound("Период отчётности не найден")
        if period.status == ReportPeriodStatus.CLOSED:
            return ReportPeriodRead.model_validate(period)
        before = {"status": period.status.value, "title": period.title}
        self.repo.close_period(period)
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.report_period_closed",
            object_type="report_period",
            object_id=period.id,
            before=before,
            after={"status": period.status.value, "title": period.title},
        )
        return ReportPeriodRead.model_validate(period)

    def get_current_state(self, current_user: User) -> CurrentReportState:
        period = self.repo.get_active_period()
        if period is None:
            return CurrentReportState(active_period=None, report=None)

        report = None
        if not is_platform_admin(current_user):
            report = self.repo.get_user_report(period.id, current_user.id)
        return CurrentReportState(
            active_period=ReportPeriodRead.model_validate(period),
            report=HalfYearReportRead.model_validate(report) if report else None,
        )

    def submit_current_report(self, current_user: User, payload: HalfYearReportPayload) -> HalfYearReportRead:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            result = self._submit_current_report(current_user, payload)
            uow.commit()
            return result

    def _submit_current_report(self, current_user: User, payload: HalfYearReportPayload) -> HalfYearReportRead:
        if is_platform_admin(current_user):
            raise PermissionDenied("Администратор не подаёт полугодовой отчёт через профиль")

        period = self.repo.get_active_period()
        if period is None:
            raise InvalidRequest("Период отчётности сейчас не открыт")

        report = self.repo.upsert_user_report(period=period, user_id=current_user.id, payload=payload)
        self.db.flush()
        self.events.audit(
            actor=current_user,
            action="project.report_submitted",
            object_type="half_year_report",
            object_id=report.id,
            after={"period_id": str(period.id), "user_id": str(current_user.id)},
        )
        self.events.publish(
            event_type="ProjectReportSubmitted",
            aggregate_type="half_year_report",
            aggregate_id=report.id,
            payload={
                "report_id": str(report.id),
                "period_id": str(period.id),
                "user_id": str(current_user.id),
            },
        )
        return HalfYearReportRead.model_validate(report)

    def list_reports(self, period_id: UUID | None = None) -> list[AdminHalfYearReportRead]:
        if period_id is not None and self.repo.get_period(period_id) is None:
            raise EntityNotFound("Период отчётности не найден")
        return [AdminHalfYearReportRead.model_validate(report) for report in self.repo.list_reports(period_id)]
