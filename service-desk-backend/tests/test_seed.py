from sqlalchemy import select

from scripts.seed import main as seed_main, seed_templates

from app.modules.access.models import ServiceDeskUser
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.templates.models import ServiceDeskTemplateVersion
from app.core.enums import TemplateVersionStatus


def test_service_desk_seed_is_idempotent(client, db_session_factory):
    seed_main(db_session_factory)
    seed_main(db_session_factory)

    categories = client.get("/categories", headers=client.admin_headers)
    assert categories.status_code == 200
    category_titles = {item["title"] for item in categories.json()}
    assert "Сопровождение учебного процесса" in category_titles
    assert "Практика: Сопровождение" in category_titles

    services = client.get(
        "/services",
        params={"q": "Бронирование аудиторий"},
        headers=client.admin_headers,
    )
    assert services.status_code == 200
    assert services.json()
    service_id = services.json()[0]["id"]

    form = client.get(f"/services/{service_id}/form", headers=client.admin_headers)
    assert form.status_code == 200
    assert any(field["key"] == "building_address" for field in form.json()["fields"])


def test_seed_models_exist_after_script(client, db_session_factory):
    seed_main(db_session_factory)

    with db_session_factory() as db:
        assert db.scalar(select(ServiceDeskCategory).limit(1)) is not None
        assert db.scalar(select(ServiceDeskService).limit(1)) is not None
        assert db.scalar(select(ServiceDeskTemplateVersion).limit(1)) is not None
        users = list(db.scalars(select(ServiceDeskUser).order_by(ServiceDeskUser.email)))
        assert users == []


def test_seed_publishes_every_active_service_and_resolves_dictionary_options(client, db_session_factory):
    seed_main(db_session_factory)
    with db_session_factory() as db:
        active_services = list(
            db.scalars(
                select(ServiceDeskService).where(
                    ServiceDeskService.is_active.is_(True),
                    ServiceDeskService.deleted_at.is_(None),
                )
            )
        )
        assert active_services
        for service in active_services:
            assert db.scalar(
                select(ServiceDeskTemplateVersion).where(
                    ServiceDeskTemplateVersion.service_id == service.id,
                    ServiceDeskTemplateVersion.status == TemplateVersionStatus.PUBLISHED,
                )
            ) is not None
    services = client.get("/services", headers=client.admin_headers)
    assert services.status_code == 200
    assert services.json()
    for service in services.json():
        form = client.get(
            f"/services/{service['id']}/form", headers=client.admin_headers
        )
        assert form.status_code == 200, form.text
    water = next(item for item in services.json() if item["title"] == "Заказ воды")
    water_form = client.get(
        f"/services/{water['id']}/form", headers=client.admin_headers
    )
    fields = {field["key"]: field for field in water_form.json()["fields"]}
    assert fields["gia_type"]["effective_options"] == [{"label": "Государственный экзамен", "value": "state_exam", "position": 0, "is_active": True, "metadata": {}} , {"label": "ВКР", "value": "vkr", "position": 1, "is_active": True, "metadata": {}}]


def test_seed_preserves_user_draft_and_creates_separate_fallback(client, db_session_factory):
    with db_session_factory() as db:
        category = ServiceDeskCategory(title="User draft category", position=0)
        db.add(category)
        db.flush()
        service = ServiceDeskService(
            category_id=category.id,
            title="User draft service",
            short_description="User-owned draft",
            position=0,
        )
        db.add(service)
        db.flush()
        draft = ServiceDeskTemplateVersion(
            service_id=service.id,
            version=1,
            status=TemplateVersionStatus.DRAFT,
            system_settings={"default_title": "User draft"},
        )
        db.add(draft)
        db.commit()
        service_id = service.id

    with db_session_factory() as db:
        service = db.get(ServiceDeskService, service_id)
        assert service is not None
        seed_templates(db, {("User draft category", service.title): service})
        db.commit()
        versions = list(
            db.scalars(
                select(ServiceDeskTemplateVersion)
                .where(ServiceDeskTemplateVersion.service_id == service_id)
                .order_by(ServiceDeskTemplateVersion.version)
            )
        )
        assert [version.status for version in versions] == [TemplateVersionStatus.DRAFT, TemplateVersionStatus.PUBLISHED]
        assert versions[0].system_settings == {"default_title": "User draft"}
        assert versions[1].system_settings["_seed_generated"] is True
