from __future__ import annotations

import logging
import sys
import time

from platform_sdk.observability import get_service_metrics, start_worker_metrics_server
from platform_sdk.worker_loop import PeriodicJob, check_health, run_jobs

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.approvals import models as approval_models  # noqa: F401
from app.modules.comments import models as comment_models  # noqa: F401
from app.modules.notifications.worker import NotificationOutboxWorker
from app.modules.sla.runner import SlaWorkerRunner
from scripts.attachment_cleanup_worker import cleanup_once

NAMES = ("sla", "notifications", "cleanup")


def main() -> int:
    if "--health" in sys.argv:
        return 0 if check_health(NAMES) else 1
    logging.basicConfig(level=logging.INFO)
    metrics = get_service_metrics(service="service-desk-worker", module="service-desk")
    start_worker_metrics_server(metrics, port=settings.worker_metrics_port)
    runner = SlaWorkerRunner(
        SessionLocal,
        poll_interval_seconds=settings.sla_worker_poll_interval_seconds,
        wait=lambda _: None,
        stop_requested=lambda: False,
        metrics=metrics,
    )

    def sla() -> None:
        if runner.run_iteration() is None:
            raise RuntimeError("SLA iteration failed")

    def notifications() -> None:
        started = time.perf_counter()
        failed = False
        try:
            with SessionLocal() as db:
                result = NotificationOutboxWorker(db).run_once()
                db.commit()
            metrics.record_business_operation(
                "notification_delivery", outcome="failed" if result["failed"] else "success"
            )
            logging.getLogger(__name__).info("notification_outbox_iteration=%s", result)
        except Exception:
            failed = True
            raise
        finally:
            metrics.observe_worker(
                worker="notification_outbox",
                duration_seconds=time.perf_counter() - started,
                failed=failed,
            )

    def cleanup() -> None:
        started = time.perf_counter()
        failed = False
        try:
            result = cleanup_once()
            metrics.record_business_operation(
                "attachment_cleanup", outcome="removed" if any(result.values()) else "idle"
            )
        except Exception:
            failed = True
            raise
        finally:
            metrics.observe_worker(
                worker="attachment_cleanup",
                duration_seconds=time.perf_counter() - started,
                failed=failed,
            )

    run_jobs(
        (
            PeriodicJob("sla", sla, settings.sla_worker_poll_interval_seconds),
            PeriodicJob("notifications", notifications, 5),
            PeriodicJob("cleanup", cleanup, 300),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
