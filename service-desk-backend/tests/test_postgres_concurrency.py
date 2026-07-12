import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier

import pytest

from app.modules.tickets.repository import TicketRepository


pytestmark = pytest.mark.skipif(
    not os.getenv("SERVICE_DESK_TEST_DATABASE_URL"),
    reason="PostgreSQL integration contour is disabled",
)


def test_parallel_ticket_number_generation_is_unique(db_session_factory):
    workers = 8
    barrier = Barrier(workers)
    year = datetime.now(UTC).year

    def generate() -> str:
        with db_session_factory() as db:
            barrier.wait()
            number = TicketRepository(db).next_ticket_number(year)
            db.commit()
            return number

    with ThreadPoolExecutor(max_workers=workers) as executor:
        numbers = list(executor.map(lambda _index: generate(), range(workers)))

    assert len(set(numbers)) == workers
    assert sorted(numbers) == [f"SD-{year}-{index:06d}" for index in range(1, workers + 1)]
