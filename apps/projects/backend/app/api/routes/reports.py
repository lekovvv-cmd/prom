from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, StrictAdminUser
from app.modules.reports.schemas import (
    AdminHalfYearReportRead,
    CurrentReportState,
    HalfYearReportPayload,
    HalfYearReportRead,
    ReportPeriodCreate,
    ReportPeriodRead,
)
from app.modules.reports.service import ReportService

router = APIRouter(tags=["reports"])


@router.get("/reports/current", response_model=CurrentReportState)
def get_current_report_state(current_user: CurrentUser, db: DbSession) -> CurrentReportState:
    return ReportService(db).get_current_state(current_user)


@router.put("/reports/current", response_model=HalfYearReportRead)
def submit_current_report(
    payload: HalfYearReportPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> HalfYearReportRead:
    return ReportService(db).submit_current_report(current_user, payload)


@router.get("/admin/reports/periods", response_model=list[ReportPeriodRead])
def list_report_periods(_current_user: StrictAdminUser, db: DbSession) -> list[ReportPeriodRead]:
    return ReportService(db).list_periods()


@router.post("/admin/reports/periods", response_model=ReportPeriodRead, status_code=201)
def open_report_period(
    payload: ReportPeriodCreate,
    current_user: StrictAdminUser,
    db: DbSession,
) -> ReportPeriodRead:
    return ReportService(db).open_period(payload, current_user)


@router.patch("/admin/reports/periods/{period_id}/close", response_model=ReportPeriodRead)
def close_report_period(
    period_id: UUID,
    current_user: StrictAdminUser,
    db: DbSession,
) -> ReportPeriodRead:
    return ReportService(db).close_period(period_id, current_user)


@router.get("/admin/reports", response_model=list[AdminHalfYearReportRead])
def list_reports(
    _current_user: StrictAdminUser,
    db: DbSession,
    period_id: UUID | None = None,
) -> list[AdminHalfYearReportRead]:
    return ReportService(db).list_reports(period_id)
