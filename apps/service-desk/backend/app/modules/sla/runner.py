from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from platform_sdk.observability import ServiceMetrics
from sqlalchemy.orm import Session

from app.modules.sla.worker import SlaWorker

logger = logging.getLogger(__name__)


class SlaWorkerRunner:
    """Run independently testable SLA worker iterations as a durable process loop."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        poll_interval_seconds: float,
        wait: Callable[[float], Any],
        stop_requested: Callable[[], bool],
        metrics: ServiceMetrics | None = None,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        self._session_factory = session_factory
        self._poll_interval_seconds = poll_interval_seconds
        self._wait = wait
        self._stop_requested = stop_requested
        self._metrics = metrics

    def run_iteration(self) -> dict[str, int] | None:
        started = time.perf_counter()
        failed = False
        db = self._session_factory()
        try:
            result = SlaWorker(db).run_once()
            logger.info("SLA worker iteration completed: %s", result)
            if self._metrics is not None:
                self._metrics.record_business_operation(
                    "sla_iteration",
                    outcome="processed" if result["processed"] else "idle",
                )
            return result
        except Exception:
            failed = True
            db.rollback()
            logger.exception("SLA worker iteration failed; the next iteration will continue")
            return None
        finally:
            db.close()
            if self._metrics is not None:
                self._metrics.observe_worker(
                    worker="sla",
                    duration_seconds=time.perf_counter() - started,
                    failed=failed,
                )

    def run_forever(self) -> None:
        consecutive_failures = 0
        while not self._stop_requested():
            result = self.run_iteration()
            consecutive_failures = consecutive_failures + 1 if result is None else 0
            if not self._stop_requested():
                multiplier = 2 ** min(consecutive_failures, 5)
                self._wait(self._poll_interval_seconds * multiplier)
