from sqlalchemy import select

from scripts.seed import main as seed_main

from app.modules.access.models import ServiceDeskUser
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.templates.models import ServiceDeskTemplateVersion


def test_service_desk_seed_is_idempotent(client, db_session_factory):
    seed_main(db_session_factory)
    seed_main(db_session_factory)

    categories = client.get("/categories")
    assert categories.status_code == 200
    category_titles = {item["title"] for item in categories.json()}
    assert "Сопровождение учебного процесса" in category_titles
    assert "Практика: Сопровождение" in category_titles

    services = client.get("/services", params={"q": "Бронирование аудиторий"})
    assert services.status_code == 200
    assert services.json()
    service_id = services.json()[0]["id"]

    form = client.get(f"/services/{service_id}/form")
    assert form.status_code == 200
    assert any(field["key"] == "building_address" for field in form.json()["fields"])


def test_seed_models_exist_after_script(client, db_session_factory):
    seed_main(db_session_factory)

    with db_session_factory() as db:
        assert db.scalar(select(ServiceDeskCategory).limit(1)) is not None
        assert db.scalar(select(ServiceDeskService).limit(1)) is not None
        assert db.scalar(select(ServiceDeskTemplateVersion).limit(1)) is not None
        users = list(db.scalars(select(ServiceDeskUser).order_by(ServiceDeskUser.email)))
        assert [user.email for user in users] == [
            "admin@utmn.ru",
            "analyst@utmn.ru",
            "employee@utmn.ru",
            "manager@utmn.ru",
        ]
        manager = next(user for user in users if user.email == "manager@utmn.ru")
        assert manager.identity_user_id == "00000000-0000-0000-0000-000000000002"
        assert {item.capability for item in manager.capabilities} >= {
            "service_desk.access",
            "service_desk.approve",
        }
