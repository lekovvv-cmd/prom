"""Small in-process scheduler for independent periodic worker jobs."""

from __future__ import annotations

import json
import logging
import os
import signal
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/prom-worker-health.json")


@dataclass(frozen=True)
class PeriodicJob:
    name: str
    run: Callable[[], object]
    interval_seconds: float


def check_health(names: tuple[str, ...], *, path: Path = HEALTH_FILE) -> bool:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        now = time.time()
        for name in names:
            task = state["tasks"][name]
            last_success = task["last_success"]
            if last_success is None:
                if now - state["started_at"] > task["stale_after_seconds"]:
                    return False
            elif now - last_success > task["stale_after_seconds"]:
                return False
        return True
    except OSError, ValueError, KeyError, TypeError:
        return False


def run_jobs(jobs: tuple[PeriodicJob, ...], *, path: Path = HEALTH_FILE) -> None:
    stop = Event()
    lock = Lock()
    state = {
        "started_at": time.time(),
        "tasks": {
            job.name: {
                "last_success": None,
                "stale_after_seconds": max(job.interval_seconds * 3, 30),
            }
            for job in jobs
        },
    }

    def save() -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            json.dump(state, handle)
            temporary = Path(handle.name)
        os.replace(temporary, path)

    with lock:
        save()

    def run_one(job: PeriodicJob) -> None:
        while not stop.is_set():
            started = time.monotonic()
            try:
                job.run()
            except Exception:
                logger.exception("Worker task failed: %s", job.name)
            else:
                with lock:
                    state["tasks"][job.name]["last_success"] = time.time()
                    save()
            stop.wait(max(job.interval_seconds - (time.monotonic() - started), 0.1))

    def request_stop(signum: int, _frame: object) -> None:
        logger.info("Received signal %s; stopping worker", signum)
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    threads = [Thread(target=run_one, args=(job,), name=job.name, daemon=True) for job in jobs]
    for thread in threads:
        thread.start()
    stop.wait()
    for thread in threads:
        thread.join(timeout=5)
