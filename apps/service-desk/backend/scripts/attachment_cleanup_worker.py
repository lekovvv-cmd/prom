from __future__ import annotations

import argparse
import logging
import time
from datetime import UTC, datetime, timedelta

from platform_sdk.observability import (
    get_service_metrics,
    start_worker_metrics_server,
)
from platform_sdk.storage import LocalFilesystemStorage

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.storage import object_storage

logger = logging.getLogger("prom.service_desk.attachment_cleanup")


def cleanup_once() -> dict[str, int]:
    storage = object_storage()
    now = datetime.now(UTC)
    result = {"deleted_blobs": 0, "rejected_blobs": 0, "orphans": 0}
    with SessionLocal() as db:
        repository = AttachmentRepository(db)
        deleted = repository.list_deleted(limit=100)
        rejected = repository.list_rejected_before(
            now - timedelta(days=settings.attachment_rejected_retention_days),
            limit=100,
        )
        known_keys = repository.list_storage_keys()

        for attachment in deleted:
            if storage.exists(attachment.storage_key):
                storage.delete(attachment.storage_key)
                result["deleted_blobs"] += 1
        for attachment in rejected:
            if storage.exists(attachment.storage_key):
                storage.delete(attachment.storage_key)
                result["rejected_blobs"] += 1
        db.commit()

    if isinstance(storage, LocalFilesystemStorage):
        for key in storage.iter_keys():
            if key in known_keys:
                continue
            path = storage.path_for(key)
            age_seconds = max(now.timestamp() - path.stat().st_mtime, 0)
            if age_seconds < settings.attachment_orphan_grace_seconds:
                continue
            storage.delete(key)
            result["orphans"] += 1
            logger.info(
                "service_desk_orphan_attachment_removed",
                extra={"event": "service_desk_orphan_attachment_removed"},
            )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=300.0)
    args = parser.parse_args()
    metrics = get_service_metrics(
        service="service-desk-attachment-cleanup-worker",
        module="service-desk",
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
            result = cleanup_once()
            metrics.record_business_operation(
                "attachment_cleanup",
                outcome="removed" if any(result.values()) else "idle",
            )
            logger.info("attachment_cleanup_iteration=%s", result)
        except Exception:
            failed = True
            raise
        finally:
            metrics.observe_worker(
                worker="attachment_cleanup",
                duration_seconds=time.perf_counter() - started,
                failed=failed,
            )
        if args.once:
            return
        time.sleep(max(args.poll_seconds, 10.0))


if __name__ == "__main__":
    main()
