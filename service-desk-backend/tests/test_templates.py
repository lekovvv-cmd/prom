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


def test_template_fields_and_dictionaries_are_versioned(client: TestClient):
    service_id = create_catalog_service(client)
    dictionary = client.post(
        "/admin/dictionaries",
        json={"code": "building_addresses", "title": "Адреса корпусов"},
    )
    assert dictionary.status_code == 201, dictionary.text
    dictionary_id = dictionary.json()["id"]
    item = client.post(
        f"/admin/dictionaries/{dictionary_id}/items",
        json={"label": "Ленина 16", "value": "lenina_16", "metadata": {"campus": "center"}},
    )
    assert item.status_code == 201, item.text
    assert item.json()["metadata"]["campus"] == "center"

    version = client.post(f"/admin/services/{service_id}/versions")
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]

    address = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "building_address",
            "label": "Адрес корпуса",
            "field_type": "select",
            "is_required": True,
            "position": 1,
            "dictionary_code": "building_addresses",
        },
    )
    assert address.status_code == 201, address.text
    address_id = address.json()["id"]

    date = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "event_date",
            "label": "Дата события",
            "field_type": "date",
            "is_required": True,
            "position": 0,
            "validation": {"min_date": "2026-01-01"},
        },
    )
    assert date.status_code == 201, date.text
    date_id = date.json()["id"]

    reordered = client.post(
        f"/admin/template-versions/{version_id}/reorder-fields",
        json={"field_ids": [address_id, date_id]},
    )
    assert reordered.status_code == 200, reordered.text
    assert [field["key"] for field in reordered.json()] == ["building_address", "event_date"]

    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200

    form = client.get(f"/services/{service_id}/form")
    assert form.status_code == 200
    assert [field["key"] for field in form.json()["fields"]] == ["building_address", "event_date"]
    assert form.json()["fields"][0]["dictionary_code"] == "building_addresses"

    blocked = client.patch(
        f"/admin/template-fields/{address_id}",
        json={"label": "Нельзя менять опубликованный snapshot"},
    )
    assert blocked.status_code == 409
