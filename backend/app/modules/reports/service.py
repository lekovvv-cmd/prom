from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import ReportPeriodStatus, UserRole
from app.core.exceptions import DomainError
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

    def list_periods(self) -> list[ReportPeriodRead]:
        return [ReportPeriodRead.model_validate(period) for period in self.repo.list_periods()]

    def open_period(self, payload: ReportPeriodCreate, current_user: User) -> ReportPeriodRead:
        self.repo.close_open_periods()
        period = self.repo.create_period(payload, current_user.id)
        self.db.commit()
        return ReportPeriodRead.model_validate(period)

    def close_period(self, period_id: UUID) -> ReportPeriodRead:
        period = self.repo.get_period(period_id)
        if period is None:
            raise DomainError("Период отчётности не найден", status_code=404)
        if period.status == ReportPeriodStatus.CLOSED:
            return ReportPeriodRead.model_validate(period)
        self.repo.close_period(period)
        self.db.commit()
        return ReportPeriodRead.model_validate(period)

    def get_current_state(self, current_user: User) -> CurrentReportState:
        period = self.repo.get_active_period()
        if period is None:
            return CurrentReportState(active_period=None, report=None)

        report = None
        if current_user.role != UserRole.ADMIN:
            report = self.repo.get_user_report(period.id, current_user.id)
        return CurrentReportState(
            active_period=ReportPeriodRead.model_validate(period),
            report=HalfYearReportRead.model_validate(report) if report else None,
        )

    def submit_current_report(self, current_user: User, payload: HalfYearReportPayload) -> HalfYearReportRead:
        if current_user.role == UserRole.ADMIN:
            raise DomainError("Администратор не подаёт полугодовой отчёт через профиль", status_code=403)

        period = self.repo.get_active_period()
        if period is None:
            raise DomainError("Период отчётности сейчас не открыт")

        report = self.repo.upsert_user_report(period=period, user_id=current_user.id, payload=payload)
        self.db.commit()
        return HalfYearReportRead.model_validate(report)

    def list_reports(self, period_id: UUID | None = None) -> list[AdminHalfYearReportRead]:
        if period_id is not None and self.repo.get_period(period_id) is None:
            raise DomainError("Период отчётности не найден", status_code=404)
        return [AdminHalfYearReportRead.model_validate(report) for report in self.repo.list_reports(period_id)]
