import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


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
        db.flush()
        db.add(
            ServiceDeskUserCapability(
                service_desk_user_id=user.id,
                capability="service_desk.access",
            )
        )
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


def test_ticket_draft_create_update_list_and_history(
    client: TestClient,
    db_session_factory,
    auth_headers_for_user,
):
    requester_id = create_requester(client, db_session_factory)
    other_requester_id = create_requester(client, db_session_factory)
    requester_headers = auth_headers_for_user(requester_id)
    service_id, version_id = create_service_with_template(client)

    created = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "title": "Нужна аудитория",
            "description": "Для проектной встречи.",
            "priority": "medium",
            "field_values": {"room": "305"},
        },
        headers=requester_headers,
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    ticket_id = payload["id"]
    assert payload["number"] is None
    assert payload["status"] == "draft"
    assert payload["template_version_id"] == version_id
    assert payload["history"][0]["event_type"] == "ticket_created"

    other_headers = auth_headers_for_user(other_requester_id)
    foreign_update = client.patch(
        f"/tickets/{ticket_id}",
        json={"priority": "low"},
        headers=other_headers,
    )
    assert foreign_update.status_code == 403
    foreign_submit = client.post(f"/tickets/{ticket_id}/submit", headers=other_headers)
    assert foreign_submit.status_code == 403

    updated = client.patch(
        f"/tickets/{ticket_id}",
        json={"priority": "high", "field_values": {"room": "408"}},
        headers=requester_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["priority"] == "high"
    assert updated.json()["field_values"] == {"room": "408"}
    assert [item["event_type"] for item in updated.json()["history"]] == [
        "ticket_created",
        "ticket_updated",
    ]

    mine = client.get("/me/tickets", params={"status": "draft"}, headers=requester_headers)
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()] == [ticket_id]

    other_mine = client.get(
        "/me/tickets",
        params={"requester_user_id": requester_id},
        headers=auth_headers_for_user(other_requester_id),
    )
    assert other_mine.status_code == 200
    assert other_mine.json() == []

    details = client.get(
        f"/tickets/{ticket_id}",
        headers=auth_headers_for_user(requester_id),
    )
    assert details.status_code == 200
    assert details.json()["id"] == ticket_id


def test_ticket_draft_requires_auth_and_rejects_requester_spoofing(
    client: TestClient,
    db_session_factory,
    auth_headers_for_user,
):
    category = client.post("/admin/categories", json={"title": "Категория"})
    assert category.status_code == 201
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Услуга"},
    )
    assert service.status_code == 201

    requester_id = create_requester(client, db_session_factory)
    other_requester_id = create_requester(client, db_session_factory)
    payload = {
        "service_id": service.json()["id"],
        "title": "Нет подмены",
    }

    assert client.post("/tickets/drafts", json=payload).status_code == 401

    spoofed = client.post(
        "/tickets/drafts",
        json={
            **payload,
            "requester_user_id": other_requester_id,
        },
        headers=auth_headers_for_user(requester_id),
    )
    assert spoofed.status_code == 422


def test_ticket_submit_validates_and_assigns_sequential_number(
    client: TestClient,
    db_session_factory,
    auth_headers_for_user,
):
    requester_id = create_requester(client, db_session_factory)
    requester_headers = auth_headers_for_user(requester_id)
    service_id, _ = create_service_with_template(client)

    missing_fields = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "title": "Нужна аудитория",
        },
        headers=requester_headers,
    )
    assert missing_fields.status_code == 201, missing_fields.text
    rejected = client.post(
        f"/tickets/{missing_fields.json()['id']}/submit",
        headers=requester_headers,
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"] == {
        "message": "Проверьте заполнение формы",
        "errors": [
            {"field_key": "description", "message": "Описание: Заполните обязательное поле"},
            {"field_key": "room", "message": "Аудитория: Заполните обязательное поле"},
        ],
    }

    ticket_ids: list[str] = []
    for room in ("305", "408"):
        created = client.post(
            "/tickets/drafts",
            json={
                "service_id": service_id,
                "title": "Нужна аудитория",
                "description": "Для рабочей встречи.",
                "field_values": {"room": room, "ignored": "not-in-template"},
            },
            headers=requester_headers,
        )
        assert created.status_code == 201, created.text
        ticket_ids.append(created.json()["id"])

    submitted = [
        client.post(f"/tickets/{ticket_id}/submit", headers=requester_headers)
        for ticket_id in ticket_ids
    ]
    assert all(response.status_code == 200 for response in submitted)
    current_year = datetime.now(UTC).year
    assert [response.json()["number"] for response in submitted] == [
        f"SD-{current_year}-000001",
        f"SD-{current_year}-000002",
    ]
    assert submitted[0].json()["status"] == "approved"
    assert submitted[0].json()["submitted_at"] is not None
    assert submitted[0].json()["approved_at"] is not None
    assert submitted[0].json()["field_values"] == {"room": "305"}
    assert [item["event_type"] for item in submitted[0].json()["history"]][-2:] == [
        "ticket_submitted",
        "ticket_approved",
    ]

    duplicate = client.post(f"/tickets/{ticket_ids[0]}/submit", headers=requester_headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Отправить можно только черновик заявки"


def test_ticket_submit_rejects_unknown_dictionary_value(
    client: TestClient,
    db_session_factory,
    auth_headers_for_user,
):
    requester_id = create_requester(client, db_session_factory)
    requester_headers = auth_headers_for_user(requester_id)
    category = client.post("/admin/categories", json={"title": "Административные услуги"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Допуск в здание"},
    )
    dictionary = client.post(
        "/admin/dictionaries",
        json={"code": "building_addresses", "title": "Адреса корпусов"},
    )
    client.post(
        f"/admin/dictionaries/{dictionary.json()['id']}/items",
        json={"label": "Ленина 16", "value": "lenina_16"},
    )
    version = client.post(
        f"/admin/services/{service.json()['id']}/versions",
        json={"system_settings": {"is_description_required": False}},
    )
    field = client.post(
        f"/admin/template-versions/{version.json()['id']}/fields",
        json={
            "key": "address",
            "label": "Адрес корпуса",
            "field_type": "select",
            "is_required": True,
            "dictionary_code": "building_addresses",
        },
    )
    assert field.status_code == 201, field.text
    published = client.post(f"/admin/template-versions/{version.json()['id']}/publish")
    assert published.status_code == 200, published.text

    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "title": "Нужен допуск",
            "field_values": {"address": "unknown"},
        },
        headers=requester_headers,
    )
    assert draft.status_code == 201, draft.text
    submitted = client.post(f"/tickets/{draft.json()['id']}/submit", headers=requester_headers)
    assert submitted.status_code == 422
    assert submitted.json()["detail"]["errors"] == [
        {"field_key": "address", "message": "Адрес корпуса: Выберите значение из списка"}
    ]
