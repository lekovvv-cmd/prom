from datetime import UTC, datetime

import pytest

from app.modules.sla.engine import add_business_minutes, business_seconds_between


@pytest.fixture
def calendar():
    return {
        "business_calendar_timezone": "Asia/Yekaterinburg",
        "business_hours": [
            *[
                {"weekday": day, "start_time": start, "end_time": end}
                for day in range(5)
                for start, end in (("09:00:00", "13:00:00"), ("14:00:00", "18:00:00"))
            ]
        ],
        "calendar_exceptions": [
            {"date": "2026-07-14", "type": "holiday", "start_time": None, "end_time": None},
            {"date": "2026-07-18", "type": "working_day", "start_time": None, "end_time": None},
            {"date": "2026-07-19", "type": "custom_hours", "start_time": "10:00:00", "end_time": "12:00:00"},
            {"date": "2026-07-19", "type": "custom_hours", "start_time": "13:00:00", "end_time": "15:00:00"},
        ],
    }


@pytest.mark.parametrize(
    ("start", "minutes", "expected"),
    [
        ("2026-07-13T05:00:00+00:00", 60, "2026-07-13T06:00:00+00:00"),
        ("2026-07-13T02:00:00+00:00", 60, "2026-07-13T05:00:00+00:00"),
        ("2026-07-13T14:00:00+00:00", 60, "2026-07-15T05:00:00+00:00"),
        ("2026-07-13T07:30:00+00:00", 60, "2026-07-13T09:30:00+00:00"),
        ("2026-07-17T12:30:00+00:00", 60, "2026-07-18T04:30:00+00:00"),
        ("2026-07-18T12:00:00+00:00", 180, "2026-07-19T07:00:00+00:00"),
    ],
)
def test_business_time_boundaries(calendar, start, minutes, expected):
    assert add_business_minutes(datetime.fromisoformat(start), minutes, calendar) == datetime.fromisoformat(expected)


def test_dst_calendar_uses_elapsed_business_time():
    calendar = {
        "business_calendar_timezone": "America/New_York",
        "business_hours": [{"weekday": 6, "start_time": "00:00:00", "end_time": "04:00:00"}],
        "calendar_exceptions": [],
    }
    # DST spring-forward day contains only three elapsed hours in this local interval.
    result = add_business_minutes(datetime(2026, 3, 8, 5, tzinfo=UTC), 180, calendar)
    assert result == datetime(2026, 3, 8, 8, tzinfo=UTC)


def test_rejects_naive_start(calendar):
    with pytest.raises(ValueError, match="timezone-aware"):
        add_business_minutes(datetime(2026, 7, 13, 9), 30, calendar)


def test_pause_counts_only_lost_business_time(calendar):
    start = datetime.fromisoformat("2026-07-17T12:30:00+00:00")
    end = datetime.fromisoformat("2026-07-20T05:30:00+00:00")
    assert business_seconds_between(start, end, calendar) == 14 * 3600
