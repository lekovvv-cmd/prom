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


def test_template_validation_rules_and_conditions(client: TestClient):
    service_id = create_catalog_service(client)
    version = client.post(f"/admin/services/{service_id}/versions")
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]

    need_comment = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "needs_comment",
            "label": "Нужен комментарий",
            "field_type": "select",
            "is_required": True,
            "position": 0,
            "options": [{"label": "Да", "value": "yes"}, {"label": "Нет", "value": "no"}],
        },
    )
    assert need_comment.status_code == 201, need_comment.text

    comment = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "comment",
            "label": "Комментарий",
            "field_type": "textarea",
            "position": 1,
            "validation": {"min_length": 5},
            "visibility_rules": {"field": "needs_comment", "operator": "equals", "value": "yes"},
            "required_rules": {"field": "needs_comment", "operator": "equals", "value": "yes"},
        },
    )
    assert comment.status_code == 201, comment.text

    email = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "contact_email",
            "label": "Email для связи",
            "field_type": "email",
            "is_required": True,
            "position": 2,
        },
    )
    assert email.status_code == 201, email.text

    hidden_optional = client.post(
        f"/admin/template-versions/{version_id}/validate",
        json={"data": {"needs_comment": "no", "contact_email": "user@utmn.ru"}},
    )
    assert hidden_optional.status_code == 200
    assert hidden_optional.json()["is_valid"] is True
    assert hidden_optional.json()["visible_fields"] == ["needs_comment", "contact_email"]

    missing_conditional = client.post(
        f"/admin/template-versions/{version_id}/validate",
        json={"data": {"needs_comment": "yes", "contact_email": "broken-email"}},
    )
    assert missing_conditional.status_code == 200
    payload = missing_conditional.json()
    assert payload["is_valid"] is False
    assert payload["visible_fields"] == ["needs_comment", "comment", "contact_email"]
    assert payload["required_fields"] == ["needs_comment", "comment", "contact_email"]
    messages = {item["field_key"]: item["message"] for item in payload["errors"]}
    assert "Комментарий: Заполните обязательное поле" == messages["comment"]
    assert "Email для связи: Укажите корректный email" == messages["contact_email"]

    invalid_option = client.post(
        f"/admin/template-versions/{version_id}/validate",
        json={"data": {"needs_comment": "maybe", "contact_email": "user@utmn.ru"}},
    )
    assert invalid_option.status_code == 200
    assert invalid_option.json()["errors"][0]["message"] == "Нужен комментарий: Выберите значение из списка"


def test_template_preview_resolves_dictionary_and_inline_options(client: TestClient):
    service_id = create_catalog_service(client)
    dictionary = client.post(
        "/admin/dictionaries",
        json={"code": "gia_type", "title": "Виды ГИА"},
    )
    assert dictionary.status_code == 201, dictionary.text
    dictionary_id = dictionary.json()["id"]
    for position, value in enumerate(["gos_exam", "vkr"]):
        item = client.post(
            f"/admin/dictionaries/{dictionary_id}/items",
            json={"label": value, "value": value, "position": position},
        )
        assert item.status_code == 201, item.text

    version = client.post(f"/admin/services/{service_id}/versions")
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]

    dictionary_field = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "gia_type",
            "label": "Вид ГИА",
            "field_type": "select",
            "dictionary_code": "gia_type",
            "position": 0,
        },
    )
    assert dictionary_field.status_code == 201, dictionary_field.text

    inline_field = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "water_type",
            "label": "Тип воды",
            "field_type": "select",
            "position": 1,
            "options": [
                {"label": "Газированная", "value": "sparkling"},
                {"label": "Негазированная", "value": "still"},
            ],
        },
    )
    assert inline_field.status_code == 201, inline_field.text

    preview = client.get(f"/admin/template-versions/{version_id}/preview")
    assert preview.status_code == 200
    fields = {field["key"]: field for field in preview.json()["fields"]}
    assert [option["value"] for option in fields["gia_type"]["effective_options"]] == ["gos_exam", "vkr"]
    assert [option["value"] for option in fields["water_type"]["effective_options"]] == ["sparkling", "still"]


def test_array_rules_survive_template_reads_preview_publish_and_public_form(client: TestClient):
    service_id = create_catalog_service(client)
    version = client.post(f"/admin/services/{service_id}/versions")
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]
    rules = [
        {"field": "kind", "operator": "equals", "value": "exam"},
        {"field": "count", "operator": "not_equals", "value": 0},
    ]
    created = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "details",
            "label": "Детали",
            "field_type": "textarea",
            "position": 0,
            "visibility_rules": rules,
            "required_rules": rules,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["visibility_rules"] == rules
    version_read = client.get(f"/admin/template-versions/{version_id}")
    assert version_read.status_code == 200
    assert version_read.json()["fields"][0]["required_rules"] == rules
    preview = client.get(f"/admin/template-versions/{version_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["fields"][0]["visibility_rules"] == rules
    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200
    form = client.get(f"/services/{service_id}/form")
    assert form.status_code == 200
    assert form.json()["fields"][0]["visibility_rules"] == rules
