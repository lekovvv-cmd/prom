import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.enums import ServiceDeskAccessType, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.notifications.models import ServiceDeskNotification
from app.modules.sla.engine import add_business_minutes, add_business_seconds, business_seconds_between
from app.modules.sla.models import (
    ServiceDeskEscalationRule,
    ServiceDeskSlaEscalationEvent,
    ServiceDeskTicketSlaPause,
)
from app.modules.sla.worker import SlaWorker
from app.modules.tickets.models import ServiceDeskTicket
from app.modules.templates.models import ServiceDeskTemplateVersion


def _snapshot(selected_at: datetime) -> dict:
    return {
        "policy_id": str(uuid.uuid4()),
        "selected_at": selected_at.isoformat(),
        "first_response_minutes": 60,
        "resolution_minutes": 600,
        "pause_statuses": ["waiting_requester"],
        "business_calendar_timezone": "Asia/Yekaterinburg",
        "business_hours": [
            {"weekday": weekday, "start_time": "09:00:00", "end_time": "17:00:00"}
            for weekday in range(5)
        ],
        "calendar_exceptions": [],
    }


def _template_ids(db) -> tuple[uuid.UUID, uuid.UUID]:
    category = ServiceDeskCategory(title=f"SLA {uuid.uuid4()}")
    db.add(category)
    db.flush()
    service = ServiceDeskService(category_id=category.id, title=f"SLA {uuid.uuid4()}")
    db.add(service)
    db.flush()
    version = ServiceDeskTemplateVersion(service_id=service.id, version=1)
    db.add(version)
    db.flush()
    return service.id, version.id


def test_resolution_escalations_use_pause_adjusted_effective_progress_once(
    db_session_factory,
):
    selected_at = datetime(2026, 7, 13, 5, tzinfo=UTC)  # Monday 09:00 local.
    pause_started_at = datetime(2026, 7, 13, 9, tzinfo=UTC)  # Four business hours elapsed.
    resumed_at = datetime(2026, 7, 15, 5, tzinfo=UTC)
    snapshot = _snapshot(selected_at)
    policy_id = uuid.UUID(snapshot["policy_id"])
    base_due_at = add_business_minutes(selected_at, snapshot["resolution_minutes"], snapshot)
    lost_business_seconds = business_seconds_between(pause_started_at, resumed_at, snapshot)
    adjusted_due_at = add_business_seconds(base_due_at, lost_business_seconds, snapshot)

    with db_session_factory() as db:
        service_id, template_version_id = _template_ids(db)
        requester = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email="pause-aware-requester@utmn.ru",
            display_name="Pause-aware requester",
            access_type=ServiceDeskAccessType.MANAGER,
            is_active=True,
        )
        db.add(requester)
        db.flush()
        ticket = ServiceDeskTicket(
            service_id=service_id,
            template_version_id=template_version_id,
            requester_user_id=requester.id,
            title="Pause-aware SLA escalation",
            status=ServiceDeskTicketStatus.IN_PROGRESS,
            field_values={},
            sla_snapshot=snapshot,
            sla_policy_id=policy_id,
            resolution_due_at=adjusted_due_at,
        )
        first_response_rule = ServiceDeskEscalationRule(
            sla_policy_id=policy_id,
            metric="first_response",
            threshold_percent=100,
            action_type="history_only",
            recipient_type="requester",
            is_active=True,
        )
        warning_rule = ServiceDeskEscalationRule(
            sla_policy_id=policy_id,
            metric="resolution",
            threshold_percent=80,
            action_type="create_in_app_notification",
            recipient_type="requester",
            is_active=True,
        )
        deadline_rule = ServiceDeskEscalationRule(
            sla_policy_id=policy_id,
            metric="resolution",
            threshold_percent=100,
            action_type="history_only",
            recipient_type="requester",
            is_active=True,
        )
        db.add_all([ticket, first_response_rule, warning_rule, deadline_rule])
        db.flush()
        db.add(
            ServiceDeskTicketSlaPause(
                ticket_id=ticket.id,
                reason_status="waiting_requester",
                started_at=pause_started_at,
                ended_at=resumed_at,
                duration_seconds=int((resumed_at - pause_started_at).total_seconds()),
            )
        )
        db.commit()

        # Five effective business hours: the pause must not advance the 80% threshold.
        assert SlaWorker(db).run_once(now=datetime(2026, 7, 15, 6, tzinfo=UTC))["processed"] == 1
        assert db.scalar(
            select(ServiceDeskSlaEscalationEvent.id).where(
                ServiceDeskSlaEscalationEvent.rule_id == first_response_rule.id
            )
        ) is not None
        assert (
            db.scalar(
                select(func.count())
                .select_from(ServiceDeskSlaEscalationEvent)
                .where(ServiceDeskSlaEscalationEvent.metric == "resolution")
            )
            == 0
        )

        # Eight effective business hours: 80% is reached exactly once.
        reached_at = datetime(2026, 7, 15, 9, tzinfo=UTC)
        SlaWorker(db).run_once(now=reached_at)
        SlaWorker(db).run_once(now=reached_at)
        warning_event = db.scalar(
            select(ServiceDeskSlaEscalationEvent).where(
                ServiceDeskSlaEscalationEvent.rule_id == warning_rule.id
            )
        )
        assert warning_event is not None
        assert (
            db.scalar(
                select(func.count())
                .select_from(ServiceDeskSlaEscalationEvent)
                .where(ServiceDeskSlaEscalationEvent.rule_id == warning_rule.id)
            )
            == 1
        )
        notifications = db.scalars(
            select(ServiceDeskNotification).where(
                ServiceDeskNotification.event_id == warning_event.id,
                ServiceDeskNotification.event_type == "sla_warning",
            )
        ).all()
        assert len(notifications) == 1

        # 100% escalation cannot precede the pause-adjusted resolution deadline.
        SlaWorker(db).run_once(now=datetime(2026, 7, 15, 10, 59, tzinfo=UTC))
        assert db.scalar(
            select(ServiceDeskSlaEscalationEvent.id).where(
                ServiceDeskSlaEscalationEvent.rule_id == deadline_rule.id
            )
        ) is None
        SlaWorker(db).run_once(now=adjusted_due_at)
        assert db.scalar(
            select(ServiceDeskSlaEscalationEvent.id).where(
                ServiceDeskSlaEscalationEvent.rule_id == deadline_rule.id
            )
        ) is not None


def test_sla_worker_does_not_hide_first_response_behind_resolution_pause(
    db_session_factory,
):
    selected_at = datetime(2026, 7, 13, 5, tzinfo=UTC)
    snapshot = _snapshot(selected_at)
    policy_id = uuid.UUID(snapshot["policy_id"])
    with db_session_factory() as db:
        service_id, template_version_id = _template_ids(db)
        requester = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email="first-response-pause@utmn.ru",
            display_name="First response pause requester",
            access_type=ServiceDeskAccessType.MANAGER,
            is_active=True,
        )
        db.add(requester)
        db.flush()
        ticket = ServiceDeskTicket(
            service_id=service_id,
            template_version_id=template_version_id,
            requester_user_id=requester.id,
            title="First response ignores resolution pause",
            status=ServiceDeskTicketStatus.WAITING_REQUESTER,
            field_values={},
            sla_snapshot=snapshot,
            sla_policy_id=policy_id,
            first_response_due_at=datetime(2026, 7, 13, 6, tzinfo=UTC),
            resolution_due_at=datetime(2026, 7, 14, 6, tzinfo=UTC),
        )
        db.add(ticket)
        db.flush()
        db.add(ServiceDeskTicketSlaPause(
            ticket_id=ticket.id,
            reason_status="waiting_requester",
            started_at=datetime(2026, 7, 13, 5, 30, tzinfo=UTC),
        ))
        db.commit()

        result = SlaWorker(db).run_once(now=datetime(2026, 7, 13, 7, tzinfo=UTC))
        assert result["processed"] == 1
        assert result["response_breaches"] == 1
        assert result["resolution_breaches"] == 0
        db.refresh(ticket)
        assert ticket.is_response_breached is True
        assert ticket.is_resolution_breached is False
