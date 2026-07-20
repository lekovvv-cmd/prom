from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ReportPeriodStatus
from app.modules.reports.models import HalfYearReport, ReportPeriod
from app.modules.reports.schemas import HalfYearReportPayload, ReportPeriodCreate


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_period(self) -> ReportPeriod | None:
        query = (
            select(ReportPeriod)
            .where(ReportPeriod.status == ReportPeriodStatus.OPEN)
            .order_by(ReportPeriod.opened_at.desc())
        )
        return self.db.scalars(query).first()

    def get_period(self, period_id: UUID) -> ReportPeriod | None:
        return self.db.get(ReportPeriod, period_id)

    def get_report(self, report_id: UUID) -> HalfYearReport | None:
        return self.db.get(HalfYearReport, report_id)

    def list_periods(self) -> list[ReportPeriod]:
        query = select(ReportPeriod).order_by(ReportPeriod.opened_at.desc())
        return list(self.db.scalars(query))

    def create_period(self, payload: ReportPeriodCreate, opened_by: UUID) -> ReportPeriod:
        period = ReportPeriod(
            title=payload.title,
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            opened_by=opened_by,
        )
        self.db.add(period)
        self.db.flush()
        return period

    def close_open_periods(self) -> None:
        for period in self.db.scalars(select(ReportPeriod).where(ReportPeriod.status == ReportPeriodStatus.OPEN)):
            self.close_period(period)

    def close_period(self, period: ReportPeriod) -> ReportPeriod:
        period.status = ReportPeriodStatus.CLOSED
        period.closed_at = datetime.now(UTC)
        self.db.flush()
        return period

    def get_user_report(self, period_id: UUID, user_id: UUID) -> HalfYearReport | None:
        query = select(HalfYearReport).where(
            HalfYearReport.period_id == period_id,
            HalfYearReport.user_id == user_id,
        )
        return self.db.scalars(query).one_or_none()

    def upsert_user_report(
        self,
        *,
        period: ReportPeriod,
        user_id: UUID,
        payload: HalfYearReportPayload,
    ) -> HalfYearReport:
        report = self.get_user_report(period.id, user_id)
        if report is None:
            report = HalfYearReport(period_id=period.id, user_id=user_id, completed_work=payload.completed_work)
            self.db.add(report)

        report.completed_work = payload.completed_work
        report.project_results = payload.project_results
        report.competencies_used = payload.competencies_used
        report.difficulties = payload.difficulties
        report.next_period_plans = payload.next_period_plans
        self.db.flush()
        return report

    def list_reports(self, period_id: UUID | None = None) -> list[HalfYearReport]:
        query = (
            select(HalfYearReport)
            .options(selectinload(HalfYearReport.user), selectinload(HalfYearReport.period))
            .order_by(HalfYearReport.submitted_at.desc())
        )
        if period_id is not None:
            query = query.where(HalfYearReport.period_id == period_id)
        return list(self.db.scalars(query))
