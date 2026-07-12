from fastapi.testclient import TestClient


def test_admin_can_manage_catalog_and_authenticated_user_sees_only_active(client: TestClient):
    category = client.post(
        "/admin/categories",
        json={"title": "Сопровождение учебного процесса", "position": 1},
    )
    assert category.status_code == 201, category.text
    category_id = category.json()["id"]

    child = client.post(
        "/admin/categories",
        json={"title": "Практика", "parent_id": category_id, "position": 2},
    )
    assert child.status_code == 201, child.text

    service = client.post(
        "/admin/services",
        json={
            "category_id": category_id,
            "title": "Бронирование аудиторий",
            "short_description": "Заявка на аудиторию для занятия или события.",
            "position": 1,
        },
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]

    public_categories = client.get("/categories", headers=client.admin_headers)
    assert public_categories.status_code == 200
    assert [item["title"] for item in public_categories.json()] == [
        "Сопровождение учебного процесса",
        "Практика",
    ]

    public_services = client.get(
        "/services", params={"q": "аудитор"}, headers=client.admin_headers
    )
    assert public_services.status_code == 200
    # Public catalog only exposes services that have a published form.
    assert public_services.json() == []

    deactivated = client.post(f"/admin/services/{service_id}/deactivate")
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
    assert deactivated.json()["deleted_at"] is not None

    hidden = client.get(
        "/services", params={"q": "аудитор"}, headers=client.admin_headers
    )
    assert hidden.status_code == 200
    assert hidden.json() == []

    admin_services = client.get("/admin/services", params={"q": "аудитор"})
    assert admin_services.status_code == 200
    assert [item["id"] for item in admin_services.json()] == [service_id]

    restored = client.post(f"/admin/services/{service_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["is_active"] is True
    assert restored.json()["deleted_at"] is None


def test_catalog_and_form_routes_require_service_desk_access(client: TestClient):
    service_id = "00000000-0000-0000-0000-000000000001"
    for path in (
        "/categories",
        "/services",
        f"/services/{service_id}",
        f"/services/{service_id}/form",
    ):
        assert client.get(path).status_code == 401


def test_missing_catalog_entities_return_404(client: TestClient):
    service = client.post(
        "/admin/services",
        json={
            "category_id": "00000000-0000-0000-0000-000000000001",
            "title": "Несуществующая категория",
        },
    )

    assert service.status_code == 404
    assert service.json()["detail"] == "Категория не найдена"
