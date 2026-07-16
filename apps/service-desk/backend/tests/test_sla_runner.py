from __future__ import annotations

from app.modules.sla.runner import SlaWorkerRunner


class FakeSession:
    def __init__(self) -> None:
        self.rollback_calls = 0
        self.close_calls = 0

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


def test_runner_uses_fresh_sessions_and_recovers_after_a_failed_iteration(monkeypatch) -> None:
    sessions: list[FakeSession] = []
    outcomes = [RuntimeError("temporary database problem"), {"processed": 3}]

    class FakeWorker:
        def __init__(self, _db: FakeSession) -> None:
            pass

        def run_once(self) -> dict[str, int]:
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    def session_factory() -> FakeSession:
        session = FakeSession()
        sessions.append(session)
        return session

    monkeypatch.setattr("app.modules.sla.runner.SlaWorker", FakeWorker)
    runner = SlaWorkerRunner(
        session_factory,
        poll_interval_seconds=30,
        wait=lambda _seconds: None,
        stop_requested=lambda: False,
    )

    assert runner.run_iteration() is None
    assert runner.run_iteration() == {"processed": 3}
    assert sessions[0].rollback_calls == 1
    assert [session.close_calls for session in sessions] == [1, 1]


def test_runner_waits_for_configured_interval_and_stops_without_sleeping_again(monkeypatch) -> None:
    stopped = False
    waits: list[float] = []
    runs = 0

    class FakeWorker:
        def __init__(self, _db: FakeSession) -> None:
            pass

        def run_once(self) -> dict[str, int]:
            nonlocal runs, stopped
            runs += 1
            if runs == 2:
                stopped = True
            return {"processed": runs}

    monkeypatch.setattr("app.modules.sla.runner.SlaWorker", FakeWorker)
    runner = SlaWorkerRunner(
        FakeSession,
        poll_interval_seconds=17,
        wait=waits.append,
        stop_requested=lambda: stopped,
    )

    runner.run_forever()

    assert runs == 2
    assert waits == [17]


def test_runner_backs_off_after_failures_and_resets_after_success(monkeypatch) -> None:
    waits: list[float] = []
    outcomes = [RuntimeError("db"), RuntimeError("db"), {"processed": 1}]
    stopped = False

    class FakeWorker:
        def __init__(self, _db: FakeSession) -> None:
            pass

        def run_once(self) -> dict[str, int]:
            nonlocal stopped
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            stopped = True
            return outcome

    monkeypatch.setattr("app.modules.sla.runner.SlaWorker", FakeWorker)
    runner = SlaWorkerRunner(
        FakeSession,
        poll_interval_seconds=5,
        wait=waits.append,
        stop_requested=lambda: stopped,
    )

    runner.run_forever()

    assert waits == [10, 20]
