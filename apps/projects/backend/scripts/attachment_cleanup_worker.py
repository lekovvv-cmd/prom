from __future__ import annotations

import argparse
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

from platform_sdk.observability import (
    get_service_metrics,
    start_worker_metrics_server,
)

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.attachments.repository import AttachmentRepository

logger = logging.getLogger("prom.projects.attachment_cleanup")


def cleanup_once() -> int:
    if settings.storage_backend != "local":
        return 0
    root = Path(settings.uploads_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        known_keys = AttachmentRepository(db).list_storage_keys()

    removed = 0
    now = datetime.now(UTC).timestamp()
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if root not in resolved.parents:
            continue
        relative_key = resolved.relative_to(root).as_posix()
        age_seconds = max(now - resolved.stat().st_mtime, 0)
        if relative_key in known_keys or age_seconds < settings.attachment_orphan_grace_seconds:
            continue
        resolved.unlink(missing_ok=True)
        removed += 1
        logger.info(
            "project_orphan_attachment_removed",
            extra={"event": "project_orphan_attachment_removed"},
        )
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=300.0)
    args = parser.parse_args()
    metrics = get_service_metrics(
        service="projects-attachment-cleanup-worker",
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
            removed = cleanup_once()
            metrics.record_business_operation(
                "attachment_cleanup",
                outcome="removed" if removed else "idle",
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
        if args.once:
            return
        time.sleep(max(args.poll_seconds, 10.0))


if __name__ == "__main__":
    main()
