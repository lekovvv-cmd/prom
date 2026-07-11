import uuid

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def _manager(db_session_factory, auth_headers_for_user, *capabilities):
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email="reports@utmn.ru",
            display_name="Reports",
            access_type=ServiceDeskAccessType.MANAGER,
        )
        db.add(user)
        db.flush()
        db.add_all(
            [
                ServiceDeskUserCapability(service_desk_user_id=user.id, capability=value)
                for value in ("service_desk.access", *capabilities)
            ]
        )
        db.commit()
        user_id = str(user.id)
    return auth_headers_for_user(user_id)


def test_stats_authorization_and_empty_contract(client, db_session_factory, auth_headers_for_user):
    assert client.get("/admin/stats/summary", headers={}).status_code == 401
    forbidden = _manager(db_session_factory, auth_headers_for_user)
    assert client.get("/admin/stats/summary", headers=forbidden).status_code == 403
    reports = _manager(db_session_factory, auth_headers_for_user, "service_desk.view_reports")
    response = client.get("/admin/stats/summary", headers=reports)
    assert response.status_code == 200
    assert response.json()["current_backlog"] == 0
    times = client.get("/admin/stats/times", headers=reports).json()
    assert times["time_to_approval"] == {
        "average_seconds": None,
        "median_seconds": None,
        "p90_seconds": None,
        "sample_size": 0,
    }
    assert (
        client.get(
            "/admin/stats/summary?date_from=2026-07-12&date_to=2026-07-11", headers=reports
        ).status_code
        == 422
    )
