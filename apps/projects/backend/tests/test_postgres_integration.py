from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import select

from platform_sdk.outbox import claim_outbox_batch

from app.core.enums import (
    ProjectMemberRole,
    ProjectPriority,
    ProjectResponseStatus,
    ProjectStatus,
    ProjectType,
    ReportPeriodStatus,
)
from app.core.database import SessionLocal
from app.modules.platform.models import ProjectAuditEvent, ProjectOutboxEvent
from app.modules.projects.models import Project, ProjectMember
from app.modules.reports.models import HalfYearReport, ReportPeriod
from app.modules.reports.repository import ReportRepository
from app.modules.reports.schemas import HalfYearReportPayload, ReportPeriodCreate
from app.modules.reports.service import ReportService
from app.modules.responses.models import ProjectResponse
from app.modules.responses.schemas import ProjectResponseCreate
from app.modules.responses.service import ProjectResponseService
from app.modules.tasks.models import ProjectTask
from app.modules.tasks.schemas import ProjectTaskUpdate
from app.modules.tasks.service import ProjectTaskService
from app.modules.users.repository import UserRepository


pytestmark = pytest.mark.skipif(
    not os.getenv("PROJECTS_TEST_DATABASE_URL"),
    reason="PostgreSQL integration contour is disabled",
)


def test_parallel_outbox_claims_do_not_duplicate_events(database) -> None:
    with SessionLocal() as db:
        db.add_all(
            [
                ProjectOutboxEvent(
                    event_type="PostgresClaimTest",
                    aggregate_type="project",
                    aggregate_id=f"project-{index}",
                    payload={"index": index},
                )
                for index in range(2)
            ]
        )
        db.commit()

    barrier = Barrier(2)

    def claim(worker_id: str) -> str:
        with SessionLocal() as db:
            barrier.wait()
            events = claim_outbox_batch(
                db,
                ProjectOutboxEvent,
                worker_id=worker_id,
                batch_size=1,
            )
            assert len(events) == 1
            event_id = events[0].event_id
            db.commit()
            return event_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        claimed = list(executor.map(claim, ("worker-1", "worker-2")))

    assert len(set(claimed)) == 2


def _active_project_and_users() -> tuple[UUID, UUID, UUID]:
    with SessionLocal() as db:
        admin = UserRepository(db).get_by_email("admin@utmn.ru")
        employee = UserRepository(db).get_by_email("employee@utmn.ru")
        assert admin is not None
        assert employee is not None
        project = Project(
            title="PostgreSQL response concurrency",
            short_description="Concurrent response test.",
            description="Verifies database-enforced response state.",
            goal="One active response.",
            expected_result="Exactly one row.",
            project_type=ProjectType.STRATEGIC,
            priority=ProjectPriority.MEDIUM,
            status=ProjectStatus.ACTIVE,
            created_by=admin.id,
            contact_email="admin@utmn.ru",
        )
        db.add(project)
        db.commit()
        return project.id, admin.id, employee.id


def test_parallel_response_submission_keeps_one_active_row_and_one_side_effect(monkeypatch) -> None:
    project_id, _admin_id, employee_id = _active_project_and_users()
    barrier = Barrier(2)
    # Both independent commands complete the friendly pre-check before either insert.
    from app.modules.responses.repository import ProjectResponseRepository

    original_precheck = ProjectResponseRepository.exists_for_project_email

    def synchronized_precheck(self, *args, **kwargs):
        result = original_precheck(self, *args, **kwargs)
        barrier.wait()
        return result

    monkeypatch.setattr(ProjectResponseRepository, "exists_for_project_email", synchronized_precheck)

    def submit() -> str:
        with SessionLocal() as db:
            employee = UserRepository(db).get_by_id(employee_id)
            assert employee is not None
            try:
                response = ProjectResponseService(db).create_for_project(
                    project_id,
                    ProjectResponseCreate(full_name="Employee User", email="employee@utmn.ru"),
                    current_user=employee,
                )
                return f"created:{response.id}"
            except Exception as exc:  # The assertion below checks the public typed outcome.
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: submit(), range(2)))

    assert sum(item.startswith("created:") for item in outcomes) == 1
    assert outcomes.count("ConflictDetected") == 1
    with SessionLocal() as db:
        responses = list(
            db.scalars(
                select(ProjectResponse).where(
                    ProjectResponse.project_id == project_id,
                    ProjectResponse.status != ProjectResponseStatus.CANCELLED,
                    ProjectResponse.deleted_at.is_(None),
                )
            )
        )
        assert len(responses) == 1
        audits = list(
            db.scalars(
                select(ProjectAuditEvent).where(
                    ProjectAuditEvent.object_id == str(responses[0].id),
                    ProjectAuditEvent.action == "project.response_submitted",
                )
            )
        )
        events = list(
            db.scalars(
                select(ProjectOutboxEvent).where(
                    ProjectOutboxEvent.aggregate_id == str(responses[0].id),
                    ProjectOutboxEvent.event_type == "ProjectResponseSubmitted",
                )
            )
        )
    assert len(audits) == 1
    assert len(events) == 1


def test_parallel_conflicting_response_decisions_allow_one_winner(monkeypatch) -> None:
    project_id, admin_id, employee_id = _active_project_and_users()
    with SessionLocal() as db:
        response = ProjectResponse(
            project_id=project_id,
            user_id=employee_id,
            full_name="Employee User",
            email="employee@utmn.ru",
            status=ProjectResponseStatus.NEW,
        )
        db.add(response)
        db.commit()
        response_id = response.id

    barrier = Barrier(2)
    from app.modules.responses.repository import ProjectResponseRepository

    original_get = ProjectResponseRepository.get_by_id

    def synchronized_get(self, *args, **kwargs):
        response = original_get(self, *args, **kwargs)
        barrier.wait()
        return response

    monkeypatch.setattr(ProjectResponseRepository, "get_by_id", synchronized_get)

    def decide(status: ProjectResponseStatus) -> str:
        with SessionLocal() as db:
            admin = UserRepository(db).get_by_id(admin_id)
            assert admin is not None
            try:
                result = ProjectResponseService(db).update_status(
                    response_id, status, admin, idempotency_key=f"decision-{status.value}"
                )
                return result.status.value
            except Exception as exc:
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(
                decide,
                (ProjectResponseStatus.ACCEPTED, ProjectResponseStatus.REJECTED),
            )
        )

    assert sum(item in {"accepted", "rejected"} for item in outcomes) == 1
    assert outcomes.count("ConflictDetected") == 1
    with SessionLocal() as db:
        persisted = db.get(ProjectResponse, response_id)
        assert persisted is not None
        audits = list(
            db.scalars(
                select(ProjectAuditEvent).where(
                    ProjectAuditEvent.object_id == str(response_id),
                    ProjectAuditEvent.action == "project.response_status_changed",
                )
            )
        )
        events = list(
            db.scalars(
                select(ProjectOutboxEvent).where(
                    ProjectOutboxEvent.aggregate_id == str(response_id),
                    ProjectOutboxEvent.event_type == "ProjectResponseAccepted",
                )
            )
        )
    assert len(audits) == 1
    assert len(events) == (1 if persisted.status == ProjectResponseStatus.ACCEPTED else 0)


def test_parallel_period_open_keeps_one_open_period_and_one_audit(monkeypatch) -> None:
    with SessionLocal() as db:
        admin = UserRepository(db).get_by_email("admin@utmn.ru")
        assert admin is not None
        admin_id = admin.id

    barrier = Barrier(2)
    from app.modules.reports.repository import ReportRepository

    original_close = ReportRepository.close_open_periods

    def synchronized_close(self):
        original_close(self)
        barrier.wait()

    monkeypatch.setattr(ReportRepository, "close_open_periods", synchronized_close)

    def open_period(title: str) -> str:
        with SessionLocal() as db:
            admin = UserRepository(db).get_by_id(admin_id)
            assert admin is not None
            try:
                return ReportService(db).open_period(ReportPeriodCreate(title=title), admin).status.value
            except Exception as exc:
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(open_period, ("Concurrent period A", "Concurrent period B")))

    assert outcomes.count("open") == 1
    assert outcomes.count("ConflictDetected") == 1
    with SessionLocal() as db:
        open_periods = list(
            db.scalars(
                select(ReportPeriod).where(ReportPeriod.status == ReportPeriodStatus.OPEN)
            )
        )
        assert len(open_periods) == 1
        audits = list(
            db.scalars(
                select(ProjectAuditEvent).where(
                    ProjectAuditEvent.object_id == str(open_periods[0].id),
                    ProjectAuditEvent.action == "project.report_period_opened",
                )
            )
        )
    assert len(audits) == 1


def test_parallel_first_report_submissions_upsert_one_owner_report(monkeypatch) -> None:
    with SessionLocal() as db:
        admin = UserRepository(db).get_by_email("admin@utmn.ru")
        employee = UserRepository(db).get_by_email("employee@utmn.ru")
        assert admin is not None
        assert employee is not None
        period = ReportService(db).open_period(ReportPeriodCreate(title="Concurrent user reports"), admin)
        employee_id = employee.id
        period_id = period.id

    barrier = Barrier(2)
    original_get = ReportRepository.get_user_report

    def synchronized_get(self, *args, **kwargs):
        report = original_get(self, *args, **kwargs)
        if report is None:
            barrier.wait()
        return report

    monkeypatch.setattr(ReportRepository, "get_user_report", synchronized_get)

    def submit(completed_work: str) -> str:
        with SessionLocal() as db:
            employee = UserRepository(db).get_by_id(employee_id)
            assert employee is not None
            return ReportService(db).submit_current_report(
                employee,
                HalfYearReportPayload(completed_work=completed_work),
            ).id.hex

    with ThreadPoolExecutor(max_workers=2) as executor:
        report_ids = list(executor.map(submit, ("First concurrent report", "Second concurrent report")))

    assert len(set(report_ids)) == 1
    with SessionLocal() as db:
        reports = list(
            db.scalars(
                select(HalfYearReport).where(
                    HalfYearReport.period_id == period_id,
                    HalfYearReport.user_id == employee_id,
                )
            )
        )
    assert len(reports) == 1


def test_parallel_membership_insert_keeps_one_member_row() -> None:
    project_id, _admin_id, employee_id = _active_project_and_users()
    barrier = Barrier(2)

    def add_member() -> str:
        with SessionLocal() as db:
            db.add(
                ProjectMember(
                    project_id=project_id,
                    user_id=employee_id,
                    member_role=ProjectMemberRole.WORKING_GROUP_MEMBER,
                )
            )
            barrier.wait()
            try:
                db.commit()
                return "created"
            except Exception as exc:
                db.rollback()
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: add_member(), range(2)))

    assert outcomes.count("created") == 1
    assert outcomes.count("IntegrityError") == 1
    with SessionLocal() as db:
        members = list(
            db.scalars(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == employee_id,
                )
            )
        )
    assert len(members) == 1


def test_parallel_task_updates_reject_the_stale_writer(monkeypatch) -> None:
    project_id, admin_id, _employee_id = _active_project_and_users()
    with SessionLocal() as db:
        task = ProjectTask(project_id=project_id, title="Concurrent task")
        db.add(task)
        db.commit()
        task_id = task.id

    barrier = Barrier(2)
    from app.modules.tasks.repository import ProjectTaskRepository

    original_get = ProjectTaskRepository.get_task

    def synchronized_get(self, *args, **kwargs):
        task = original_get(self, *args, **kwargs)
        barrier.wait()
        return task

    monkeypatch.setattr(ProjectTaskRepository, "get_task", synchronized_get)

    def update_task(title: str) -> str:
        with SessionLocal() as db:
            admin = UserRepository(db).get_by_id(admin_id)
            assert admin is not None
            try:
                return ProjectTaskService(db).update_task(
                    project_id,
                    task_id,
                    ProjectTaskUpdate(title=title),
                    admin,
                ).title
            except Exception as exc:
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(update_task, ("Task update A", "Task update B")))

    assert sum(item.startswith("Task update") for item in outcomes) == 1
    assert outcomes.count("ConflictDetected") == 1
    with SessionLocal() as db:
        persisted = db.get(ProjectTask, task_id)
        assert persisted is not None
        audits = list(
            db.scalars(
                select(ProjectAuditEvent).where(
                    ProjectAuditEvent.object_id == str(task_id),
                    ProjectAuditEvent.action == "project.task_updated",
                )
            )
        )
    assert persisted.version == 2
    assert len(audits) == 1
