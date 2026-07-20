from __future__ import annotations

import logging
import signal
import time
from threading import Event

from platform_sdk.observability import (
    get_service_metrics,
    start_worker_metrics_server,
)

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.approvals import models as approval_models  # noqa: F401
from app.modules.comments import models as comment_models  # noqa: F401
from app.modules.notifications.worker import NotificationOutboxWorker


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    stop_event = Event()
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    metrics = get_service_metrics(
        service="service-desk-notification-worker",
        module="service-desk",
    )
    start_worker_metrics_server(metrics, port=settings.worker_metrics_port)
    while not stop_event.is_set():
        started = time.perf_counter()
        failed = False
        try:
            with SessionLocal() as db:
                result = NotificationOutboxWorker(db).run_once()
                db.commit()
            metrics.record_business_operation(
                "notification_delivery",
                outcome="failed" if result["failed"] else "success",
            )
        except Exception:
            failed = True
            raise
        finally:
            metrics.observe_worker(
                worker="notification_outbox",
                duration_seconds=time.perf_counter() - started,
                failed=failed,
            )
        logging.getLogger(__name__).info("notification_outbox_iteration=%s", result)
        stop_event.wait(5)


if __name__ == "__main__":
    main()
