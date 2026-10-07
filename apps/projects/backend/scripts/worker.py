from __future__ import annotations

import logging
import socket
import sys
import time

from platform_sdk.observability import get_service_metrics, start_worker_metrics_server
from platform_sdk.worker_loop import PeriodicJob, check_health, run_jobs

from app.core.config import settings
from scripts.attachment_cleanup_worker import cleanup_once
from scripts.outbox_worker import process_batch

NAMES = ("outbox", "cleanup")


def main() -> int:
    if "--health" in sys.argv:
        return 0 if check_health(NAMES) else 1
    logging.basicConfig(level=logging.INFO)
    metrics = get_service_metrics(service="projects-worker", module="projects")
    start_worker_metrics_server(metrics, port=settings.worker_metrics_port)
    worker_id = socket.gethostname()

    def outbox() -> None:
        started = time.perf_counter()
        failed = False
        try:
            processed = process_batch(worker_id=worker_id)
            metrics.record_business_operation(
                "outbox_delivery", outcome="processed" if processed else "idle"
            )
        except Exception:
            failed = True
            raise
        finally:
            metrics.observe_worker(
                worker="outbox", duration_seconds=time.perf_counter() - started, failed=failed
            )

    def cleanup() -> None:
        started = time.perf_counter()
        failed = False
        try:
            removed = cleanup_once()
            metrics.record_business_operation(
                "attachment_cleanup", outcome="removed" if removed else "idle"
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

    run_jobs((PeriodicJob("outbox", outbox, 2), PeriodicJob("cleanup", cleanup, 300)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
