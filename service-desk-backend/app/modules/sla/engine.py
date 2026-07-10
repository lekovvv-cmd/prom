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
    if minutes <= 0:
        return start.astimezone(UTC)
    timezone = ZoneInfo(snapshot["business_calendar_timezone"])
    cursor = start.astimezone(timezone)
    remaining = timedelta(minutes=minutes)
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
