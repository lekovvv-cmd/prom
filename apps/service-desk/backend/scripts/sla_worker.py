from __future__ import annotations

import logging
import signal
from threading import Event

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.approvals import models as approval_models  # noqa: F401
from app.modules.comments import models as comment_models  # noqa: F401
from app.modules.sla.runner import SlaWorkerRunner


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    stop_event = Event()

    def request_stop(signum: int, _frame: object) -> None:
        logging.getLogger(__name__).info("Received signal %s; stopping SLA worker", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    SlaWorkerRunner(
        SessionLocal,
        poll_interval_seconds=settings.sla_worker_poll_interval_seconds,
        wait=stop_event.wait,
        stop_requested=stop_event.is_set,
    ).run_forever()


if __name__ == "__main__":
    main()
