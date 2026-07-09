import uuid

from fastapi.testclient import TestClient

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser


def create_requester(client: TestClient, db_session_factory) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email="requester@utmn.ru",
            display_name="Заявитель Service Desk",
            access_type=ServiceDeskAccessType.MANAGER,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return str(user.id)


def create_service_with_template(client: TestClient) -> tuple[str, str]:
    category = client.post("/admin/categories", json={"title": "Учебный процесс"})
    assert category.status_code == 201, category.text
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Бронирование аудитории"},
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]
    version = client.post(f"/admin/services/{service_id}/versions")
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]
    field = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "room",
            "label": "Аудитория",
            "field_type": "text",
            "is_required": True,
            "position": 0,
        },
    )
    assert field.status_code == 201, field.text
    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text
    return service_id, version_id


def test_ticket_draft_create_update_list_and_history(client: TestClient, db_session_factory):
    requester_id = create_requester(client, db_session_factory)
    service_id, version_id = create_service_with_template(client)

    created = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "requester_user_id": requester_id,
            "title": "Нужна аудитория",
            "description": "Для проектной встречи.",
            "priority": "medium",
            "field_values": {"room": "305"},
        },
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    ticket_id = payload["id"]
    assert payload["number"] is None
    assert payload["status"] == "draft"
    assert payload["template_version_id"] == version_id
    assert payload["history"][0]["event_type"] == "ticket_created"

    updated = client.patch(
        f"/tickets/{ticket_id}",
        json={"priority": "high", "field_values": {"room": "408"}},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["priority"] == "high"
    assert updated.json()["field_values"] == {"room": "408"}
    assert [item["event_type"] for item in updated.json()["history"]] == [
        "ticket_created",
        "ticket_updated",
    ]

    mine = client.get("/me/tickets", params={"requester_user_id": requester_id, "status": "draft"})
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()] == [ticket_id]

    details = client.get(f"/tickets/{ticket_id}")
    assert details.status_code == 200
    assert details.json()["id"] == ticket_id


def test_ticket_draft_requires_active_service_desk_user(client: TestClient):
    category = client.post("/admin/categories", json={"title": "Категория"})
    assert category.status_code == 201
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Услуга"},
    )
    assert service.status_code == 201

    created = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "requester_user_id": "00000000-0000-0000-0000-000000000001",
            "title": "Нет доступа",
        },
    )

    assert created.status_code == 403
    assert created.json()["detail"] == "Нет доступа к Service Desk"
