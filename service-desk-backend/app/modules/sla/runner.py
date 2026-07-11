from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

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
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        self._session_factory = session_factory
        self._poll_interval_seconds = poll_interval_seconds
        self._wait = wait
        self._stop_requested = stop_requested

    def run_iteration(self) -> dict[str, int] | None:
        db = self._session_factory()
        try:
            result = SlaWorker(db).run_once()
            logger.info("SLA worker iteration completed: %s", result)
            return result
        except Exception:
            db.rollback()
            logger.exception("SLA worker iteration failed; the next iteration will continue")
            return None
        finally:
            db.close()

    def run_forever(self) -> None:
        while not self._stop_requested():
            self.run_iteration()
            if not self._stop_requested():
                self._wait(self._poll_interval_seconds)
