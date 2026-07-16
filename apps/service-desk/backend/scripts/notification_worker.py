from __future__ import annotations

import logging
import signal
from threading import Event

from app.core.database import SessionLocal
from app.modules.approvals import models as approval_models  # noqa: F401
from app.modules.comments import models as comment_models  # noqa: F401
from app.modules.notifications.worker import NotificationOutboxWorker


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    stop_event = Event()
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    while not stop_event.is_set():
        with SessionLocal() as db:
            result = NotificationOutboxWorker(db).run_once()
            db.commit()
        logging.getLogger(__name__).info("notification_outbox_iteration=%s", result)
        stop_event.wait(5)


if __name__ == "__main__":
    main()
