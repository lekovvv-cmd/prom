from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from platform_sdk.outbox import claim_outbox_batch

from app.core.database import SessionLocal
from app.modules.platform.models import ProjectOutboxEvent


pytestmark = pytest.mark.skipif(
    not os.getenv("PROJECTS_TEST_DATABASE_URL"),
    reason="PostgreSQL integration contour is disabled",
)


def test_parallel_outbox_claims_do_not_duplicate_events(database) -> None:
    with SessionLocal() as db:
        db.add_all(
            [
                ProjectOutboxEvent(
                    event_type="PostgresClaimTest",
                    aggregate_type="project",
                    aggregate_id=f"project-{index}",
                    payload={"index": index},
                )
                for index in range(2)
            ]
        )
        db.commit()

    barrier = Barrier(2)

    def claim(worker_id: str) -> str:
        with SessionLocal() as db:
            barrier.wait()
            events = claim_outbox_batch(
                db,
                ProjectOutboxEvent,
                worker_id=worker_id,
                batch_size=1,
            )
            assert len(events) == 1
            event_id = events[0].event_id
            db.commit()
            return event_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        claimed = list(executor.map(claim, ("worker-1", "worker-2")))

    assert len(set(claimed)) == 2
