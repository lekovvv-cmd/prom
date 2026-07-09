from fastapi.testclient import TestClient


def create_catalog_service(client: TestClient) -> str:
    category = client.post("/admin/categories", json={"title": "ГИА: Администрирование"})
    assert category.status_code == 201, category.text
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Заказ воды"},
    )
    assert service.status_code == 201, service.text
    return service.json()["id"]


def test_template_versions_publish_and_archive_previous(client: TestClient):
    service_id = create_catalog_service(client)

    first = client.post(
        f"/admin/services/{service_id}/versions",
        json={"system_settings": {"default_title": "Заказ воды", "is_description_required": True}},
    )
    assert first.status_code == 201, first.text
    first_id = first.json()["id"]
    assert first.json()["version"] == 1
    assert first.json()["status"] == "draft"

    updated = client.patch(
        f"/admin/template-versions/{first_id}",
        json={"system_settings": {"default_title": "Заказ воды на ГИА", "is_description_required": True}},
    )
    assert updated.status_code == 200
    assert updated.json()["system_settings"]["default_title"] == "Заказ воды на ГИА"

    published = client.post(f"/admin/template-versions/{first_id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert published.json()["published_at"] is not None

    blocked = client.patch(
        f"/admin/template-versions/{first_id}",
        json={"system_settings": {"default_title": "Нельзя менять"}},
    )
    assert blocked.status_code == 409

    form = client.get(f"/services/{service_id}/form")
    assert form.status_code == 200
    assert form.json()["template_version"]["id"] == first_id
    assert form.json()["fields"] == []

    second = client.post(f"/admin/services/{service_id}/versions")
    assert second.status_code == 201, second.text
    assert second.json()["version"] == 2
    second_id = second.json()["id"]

    republished = client.post(f"/admin/template-versions/{second_id}/publish")
    assert republished.status_code == 200
    assert republished.json()["status"] == "published"

    versions = client.get(f"/admin/services/{service_id}/versions")
    assert versions.status_code == 200
    by_id = {item["id"]: item for item in versions.json()}
    assert by_id[first_id]["status"] == "archived"
    assert by_id[first_id]["archived_at"] is not None
    assert by_id[second_id]["status"] == "published"
