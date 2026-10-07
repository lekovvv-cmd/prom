from __future__ import annotations

import json
import time

from platform_sdk.worker_loop import check_health


def test_health_detects_one_stale_job_without_masking_it_by_another(tmp_path) -> None:
    path = tmp_path / "health.json"
    now = time.time()
    state = {
        "started_at": now - 100,
        "tasks": {
            "sla": {"last_success": now - 100, "stale_after_seconds": 30},
            "notifications": {"last_success": now, "stale_after_seconds": 30},
        },
    }
    path.write_text(json.dumps(state), encoding="utf-8")
    assert not check_health(("sla", "notifications"), path=path)

    state["tasks"]["sla"]["last_success"] = now
    path.write_text(json.dumps(state), encoding="utf-8")
    assert check_health(("sla", "notifications"), path=path)
