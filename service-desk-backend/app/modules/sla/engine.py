from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def _local_intervals(snapshot: dict, day: date) -> list[tuple[datetime, datetime]]:
    timezone = ZoneInfo(snapshot["business_calendar_timezone"])
    exceptions = [item for item in snapshot.get("calendar_exceptions", []) if item["date"] == day.isoformat()]
    if exceptions:
        kind = exceptions[0]["type"]
        if kind == "holiday":
            return []
        if kind == "custom_hours":
            raw = [(item["start_time"], item["end_time"]) for item in exceptions]
        else:  # working_day uses the normal weekday schedule
            raw = [
                (item["start_time"], item["end_time"])
                for item in snapshot["business_hours"]
                if item["weekday"] == day.weekday()
            ]
            if not raw:
                fallback_weekday = min(item["weekday"] for item in snapshot["business_hours"])
                raw = [
                    (item["start_time"], item["end_time"])
                    for item in snapshot["business_hours"]
                    if item["weekday"] == fallback_weekday
                ]
    else:
        raw = [
            (item["start_time"], item["end_time"])
            for item in snapshot["business_hours"]
            if item["weekday"] == day.weekday()
        ]
    return [
        (
            datetime.combine(day, time.fromisoformat(start), timezone),
            datetime.combine(day, time.fromisoformat(end), timezone),
        )
        for start, end in sorted(raw)
    ]


def add_business_minutes(start: datetime, minutes: int, snapshot: dict) -> datetime:
    """Add elapsed business minutes in the snapshot calendar and return UTC."""
    if start.tzinfo is None:
        raise ValueError("SLA start must be timezone-aware")
    return add_business_seconds(start, minutes * 60, snapshot)


def add_business_seconds(start: datetime, seconds: int, snapshot: dict) -> datetime:
    if start.tzinfo is None:
        raise ValueError("SLA start must be timezone-aware")
    if seconds <= 0:
        return start.astimezone(UTC)
    timezone = ZoneInfo(snapshot["business_calendar_timezone"])
    cursor = start.astimezone(timezone)
    remaining = timedelta(seconds=seconds)
    for _ in range(36600):
        intervals = _local_intervals(snapshot, cursor.date())
        for interval_start, interval_end in intervals:
            if cursor >= interval_end:
                continue
            effective_start = max(cursor, interval_start)
            available = interval_end.astimezone(UTC) - effective_start.astimezone(UTC)
            if remaining <= available:
                return (effective_start.astimezone(UTC) + remaining).astimezone(UTC)
            remaining -= available
            cursor = interval_end
        cursor = datetime.combine(cursor.date() + timedelta(days=1), time.min, timezone)
    raise ValueError("Unable to find enough business time within 100 years")


def business_seconds_between(start: datetime, end: datetime, snapshot: dict) -> int:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("SLA range must be timezone-aware")
    if end <= start:
        return 0
    timezone = ZoneInfo(snapshot["business_calendar_timezone"])
    cursor = start.astimezone(timezone)
    finish = end.astimezone(timezone)
    total = 0
    while cursor.date() <= finish.date():
        for interval_start, interval_end in _local_intervals(snapshot, cursor.date()):
            lower = max(interval_start.astimezone(UTC), start.astimezone(UTC))
            upper = min(interval_end.astimezone(UTC), end.astimezone(UTC))
            if upper > lower:
                total += int((upper - lower).total_seconds())
        cursor = datetime.combine(cursor.date() + timedelta(days=1), time.min, timezone)
    return total


def effective_business_seconds_between(
    start: datetime,
    end: datetime,
    snapshot: dict,
    pause_intervals: list[tuple[datetime, datetime]],
) -> int:
    """Return business time elapsed outside SLA pause intervals."""
    elapsed = business_seconds_between(start, end, snapshot)
    paused = 0
    for pause_start, pause_end in pause_intervals:
        lower = max(start, pause_start)
        upper = min(end, pause_end)
        if upper > lower:
            paused += business_seconds_between(lower, upper, snapshot)
    return max(0, elapsed - paused)
