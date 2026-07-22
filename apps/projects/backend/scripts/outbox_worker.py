from __future__ import annotations

import argparse
import logging
import socket
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from platform_sdk.observability import (
    get_service_metrics,
    start_worker_metrics_server,
)
from platform_sdk.outbox import (
    claim_outbox_batch,
    mark_outbox_failed,
    mark_outbox_processed,
)

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import AttachmentStatus
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.storage import object_storage
from app.modules.platform.models import ProjectOutboxEvent

logger = logging.getLogger("prom.projects.outbox")


def _dispatch(event: ProjectOutboxEvent, db) -> None:  # type: ignore[no-untyped-def]
    if event.event_type != "AttachmentDeletionRequested":
        return
    attachment_id = UUID(str(event.payload["attachment_id"]))
    attachment = AttachmentRepository(db).get_for_cleanup(attachment_id)
    if attachment is None or attachment.status == AttachmentStatus.DELETED:
        return
    storage_key = event.payload.get("storage_key")
    if storage_key:
        object_storage().delete(str(storage_key))
    else:
        Path(str(event.payload["storage_path"])).unlink(missing_ok=True)
    attachment.status = AttachmentStatus.DELETED
    attachment.deleted_at = datetime.now(UTC)
    db.flush()


def process_batch(*, worker_id: str, batch_size: int = 50) -> int:
    with SessionLocal() as db:
        events = claim_outbox_batch(
            db,
            ProjectOutboxEvent,
            worker_id=worker_id,
            batch_size=batch_size,
        )
        for event in events:
            try:
                _dispatch(event, db)
                logger.info(
                    "project_integration_event",
                    extra={
                        "event": event.event_type,
                        "request_id": event.event_id,
                    },
                )
                mark_outbox_processed(event)
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                mark_outbox_failed(event, exc)
        db.commit()
        return len(events)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    worker_id = f"{socket.gethostname()}:{id(args)}"
    metrics = get_service_metrics(
        service="projects-outbox-worker",
        module="projects",
    )
    if not args.once:
        start_worker_metrics_server(
            metrics,
            port=settings.worker_metrics_port,
        )

    while True:
        started = time.perf_counter()
        failed = False
        try:
            processed = process_batch(
                worker_id=worker_id,
                batch_size=args.batch_size,
            )
            metrics.record_business_operation(
                "outbox_delivery",
                outcome="processed" if processed else "idle",
            )
        except Exception:
            failed = True
            raise
        finally:
            metrics.observe_worker(
                worker="outbox",
                duration_seconds=time.perf_counter() - started,
                failed=failed,
            )
        if args.once:
            return
        if processed == 0:
            time.sleep(max(args.poll_seconds, 0.1))


if __name__ == "__main__":
    main()
