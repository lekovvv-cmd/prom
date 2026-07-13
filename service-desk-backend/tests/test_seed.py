import subprocess
import sys

from sqlalchemy import select

from scripts.seed import (
    APPROVED_TEMPLATE_CATEGORY_BY_SERVICE,
    APPROVED_TEMPLATE_REVISION,
    APPROVED_TEMPLATE_SOURCE,
    APPROVED_TEMPLATE_REVISION_BY_SERVICE,
    main as seed_main,
    seed_categories,
    seed_dictionaries,
    seed_services,
    seed_templates,
)

from app.modules.access.models import ServiceDeskUser
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.templates.models import ServiceDeskDictionary, ServiceDeskTemplateField, ServiceDeskTemplateVersion
from app.core.enums import TemplateVersionStatus


def test_seed_script_registers_referenced_user_table_in_isolated_process():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from scripts.seed import ServiceDeskService; "
                "assert 'service_desk_users' in ServiceDeskService.metadata.tables"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


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
    assert fields["water_type"]["effective_options"] == [
        {"label": "Газированная", "value": "sparkling", "position": 0, "is_active": True, "metadata": {}},
        {"label": "Негазированная", "value": "still", "position": 1, "is_active": True, "metadata": {}},
        {"label": "Другое", "value": "other", "position": 2, "is_active": True, "metadata": {}},
    ]
    movement = next(
        item
        for item in services.json()
        if item["title"] == "Ввоз (вывоз) и внос (вынос) материальных ценностей"
    )
    movement_form = client.get(
        f"/services/{movement['id']}/form", headers=client.admin_headers
    )
    movement_fields = {field["key"]: field for field in movement_form.json()["fields"]}
    assert movement_fields["movement_type"]["effective_options"] == [
        {"label": "Ввоз", "value": "import", "position": 0, "is_active": True, "metadata": {}},
        {"label": "Вывоз", "value": "export", "position": 1, "is_active": True, "metadata": {}},
        {"label": "Внос", "value": "bring_in", "position": 2, "is_active": True, "metadata": {}},
        {"label": "Вынос", "value": "take_out", "position": 3, "is_active": True, "metadata": {}},
    ]
    with db_session_factory() as db:
        active_dictionary_codes = set(
            db.scalars(
                select(ServiceDeskDictionary.code).where(
                    ServiceDeskDictionary.is_active.is_(True)
                )
            )
        )
        published_dictionary_codes = set(
            db.scalars(
                select(ServiceDeskTemplateField.dictionary_code)
                .join(ServiceDeskTemplateVersion)
                .where(
                    ServiceDeskTemplateVersion.status == TemplateVersionStatus.PUBLISHED,
                    ServiceDeskTemplateField.dictionary_code.is_not(None),
                )
            )
        )
    assert active_dictionary_codes == published_dictionary_codes


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


def test_approved_templates_have_exact_versioned_schemas(client, db_session_factory):
    seed_main(db_session_factory)
    seed_main(db_session_factory)

    expected = {
        "Заказ воды": [
            ("bottle_count", "Количество бутылок", "number", True, None, {"min": 1}, None),
            ("bottle_volume", "Объем бутылок", "text", True, None, None, None),
            ("water_type", "Тип воды", "select", True, "water_type", None, None),
            ("event_starts_at", "Дата и время начала мероприятия", "datetime", True, None, None, None),
            ("event_ends_at", "Дата и время окончания мероприятия", "datetime", True, None, None, None),
            ("commission_members_count", "Количество членов комиссии", "number", True, None, {"min": 1}, None),
            ("gia_sessions_count", "Количество заседаний ГЭК", "number", True, None, {"min": 1}, None),
            ("graduating_students_count", "Количество выпускающихся студентов", "number", True, None, {"min": 1}, None),
        ],
        "Установка камер": [
            ("institute", "Институт", "select", True, "institutes", {"default_value": "shpiu"}, None),
            ("gia_type", "Вид ГИА", "select", True, "gia_type", None, None),
            ("study_direction", "Направление (специальность)", "select", True, "study_directions", None, None),
            ("installation_address", "Адрес установки камер", "select", True, "camera_installation_addresses", {"default_value": "lenina_38"}, None),
            ("room_number", "Номер аудитории для установки камер", "text", True, None, None, None),
            ("event_starts_at", "Дата и время начала мероприятия", "datetime", True, None, None, None),
            ("event_ends_at", "Дата и время окончания мероприятия", "datetime", True, None, None, None),
            ("comment", "комментарии", "textarea", False, None, None, None),
        ],
        "Бронирование аудиторий": [
            ("booking_purpose", "Цель брони аудитории", "textarea", True, None, None, None),
            ("approved_with_full_name", "ФИО (с кем согласовано)", "text", True, None, None, None),
            ("building_address", "Адрес корпуса брони аудитории", "select", True, "building_addresses", None, None),
            ("room_number", "Номер аудитории", "text", True, None, None, None),
            ("event_starts_at", "Дата и время начала мероприятия", "datetime", True, None, None, None),
            ("event_ends_at", "Дата и время окончания мероприятия", "datetime", True, None, None, None),
            ("comment", "Комментарий", "textarea", False, None, None, None),
        ],
        "На печать в Издательство": [
            ("event_name", "Название мероприятия", "text", True, None, None, None),
            ("publisher_approval_status", "Согласовано/не согласовано с издательством", "select", True, "publisher_approval_status", None, None),
            ("product_type", "Вид продукции", "text", True, None, None, None),
            ("production_due_date", "Сроки изготовления", "date", True, None, None, None),
            ("product_quantity", "Количество продукции", "number", True, None, {"min": 1}, None),
            ("template_link", "Ссылка на шаблон", "text", True, None, None, None),
            ("additional_characteristics", "Дополнительные характеристики", "textarea", False, None, None, None),
        ],
        "Роль табельщика (табель рабочего времени, график отпусков)": [
            ("employee_full_name", "ФИО", "text", True, None, None, None),
            ("vacation_starts_on", "Дата начала отпуска", "date", True, None, None, None),
            ("vacation_ends_on", "Дата окончания отпуска", "date", True, None, None, None),
        ],
        "Ввоз (вывоз) и внос (вынос) материальных ценностей": [
            ("event_name", "Название мероприятия", "text", True, None, None, None),
            ("movement_type", "Тип перемещения", "select", True, "movement_type", None, None),
            ("movement_starts_at", "Дата и время вноса (ввоза)", "datetime", True, None, None, None),
            ("movement_ends_at", "Дата и время выноса (вывоза)", "datetime", True, None, None, None),
            ("inventory_list_file", "Прикрепите файл с перечнем МЦ", "file", True, None, None, None),
            ("material_type", "Вид материальных ценностей", "text", True, None, None, None),
            ("packaging", "Тара", "text", True, None, None, None),
            ("vehicle_details", "Номер, модель ТС при ввозе (вывозе)", "text", True, None, None, None),
        ],
        "Допуск в здание": [
            ("person_full_name", "ФИО (на кого оформляется допуск)", "textarea", True, None, None, None),
            ("equipment", "Оборудование", "textarea", False, None, None, None),
            ("address", "Адрес", "text", True, None, None, None),
            ("access_starts_on", "Дата начала доступа", "date", True, None, None, None),
            ("access_ends_on", "Дата прекращения доступа", "date", True, None, None, None),
        ],
        "Транспортное обслуживание": [
            ("event_name", "Название мероприятия", "text", True, None, None, None),
            ("people_count", "Количество человек (всего)", "number", True, None, {"min": 1}, None),
            ("students_count", "Количество студентов", "number", True, None, {"min": 1}, None),
            ("event_starts_at", "Дата и время начала мероприятия", "datetime", True, None, None, None),
            ("event_ends_at", "Дата и время окончания мероприятия", "datetime", True, None, None, None),
            ("route", "Маршрут (откуда-куда)", "textarea", True, None, None, None),
        ],
        "Оформление и регистрация исходящего документа": [
            ("document", "Документ", "text", True, None, None, None),
            ("document_file", "Проект или скан документа", "file", True, None, None, "Приложите проект документа в формате Word либо скан подписанного документа."),
        ],
        "График отпусков": [
            ("employee_full_name", "ФИО", "text", True, None, None, None),
            ("vacation_starts_on", "Дата начала отпуска", "date", True, None, None, None),
            ("vacation_ends_on", "Дата окончания отпуска", "date", True, None, None, None),
        ],
        "Получение со склада (кроме компьютерной техники)": [
            ("materially_responsible_person", "Материально ответственное лицо ФИО", "text", True, None, None, None),
            ("position", "Должность", "text", True, None, None, None),
            ("event_name", "Мероприятие", "text", True, None, None, None),
            ("inventory_list_file", "Список для выдачи со склада", "file", True, None, None, "Укажите материально ответственное лицо и приложите список имущества или канцелярии для выдачи."),
        ],
    }

    with db_session_factory() as db:
        for service_title, expected_fields in expected.items():
            category = db.scalar(
                select(ServiceDeskCategory).where(
                    ServiceDeskCategory.title == APPROVED_TEMPLATE_CATEGORY_BY_SERVICE[service_title]
                )
            )
            service = db.scalar(
                select(ServiceDeskService).where(
                    ServiceDeskService.category_id == category.id,
                    ServiceDeskService.title == service_title,
                )
            )
            version = db.scalar(
                select(ServiceDeskTemplateVersion).where(
                    ServiceDeskTemplateVersion.service_id == service.id,
                    ServiceDeskTemplateVersion.status == TemplateVersionStatus.PUBLISHED,
                )
            )
            assert version.system_settings["default_title"] == service_title
            assert version.system_settings["_seed_generated"] is True
            assert version.system_settings["_approved_template_revision"] == APPROVED_TEMPLATE_REVISION_BY_SERVICE.get(
                service_title,
                APPROVED_TEMPLATE_REVISION,
            )
            assert version.system_settings["_approved_template_source"] == APPROVED_TEMPLATE_SOURCE
            actual_fields = [
                (
                    item.key,
                    item.label,
                    item.field_type.value,
                    item.is_required,
                    item.dictionary_code,
                    item.validation,
                    item.help_text,
                )
                for item in sorted(version.fields, key=lambda item: item.position)
            ]
            assert actual_fields == expected_fields

        dictionaries = {
            item.code: [entry.label for entry in sorted(item.items, key=lambda entry: entry.position)]
            for item in db.scalars(select(ServiceDeskDictionary))
        }
        assert dictionaries["building_addresses"] == [
            "Ленина 16", "Ленина 23", "Ленина 38", "Перекопская 15", "Республики 9", "Другое (укажите в комментарии)"
        ]
        assert dictionaries["camera_installation_addresses"] == ["Ленина 38", "Ленина 16", "Ленина 23"]
        assert dictionaries["gia_type"] == ["гос.экзамен", "ВКР"]
        assert dictionaries["publisher_approval_status"] == ["Согласовано", "Не согласовано"]


def test_approved_template_sync_archives_old_seed_version(client, db_session_factory):
    with db_session_factory() as db:
        seed_dictionaries(db)
        services = seed_services(db, seed_categories(db))
        service = services[("ГИА: Администрирование", "Заказ воды")]
        legacy = ServiceDeskTemplateVersion(
            service_id=service.id,
            version=1,
            status=TemplateVersionStatus.PUBLISHED,
            system_settings={"_seed_generated": True, "default_title": "Заказ воды"},
        )
        db.add(legacy)
        db.flush()
        db.add(
            ServiceDeskTemplateField(
                template_version_id=legacy.id,
                key="legacy_field",
                label="Legacy field",
                field_type="text",
                position=0,
            )
        )
        seed_templates(db, services)
        db.commit()

        versions = list(
            db.scalars(
                select(ServiceDeskTemplateVersion)
                .where(ServiceDeskTemplateVersion.service_id == service.id)
                .order_by(ServiceDeskTemplateVersion.version)
            )
        )
        assert [item.status for item in versions] == [
            TemplateVersionStatus.ARCHIVED,
            TemplateVersionStatus.PUBLISHED,
        ]
        assert versions[0].fields[0].key == "legacy_field"
        assert versions[1].system_settings["_approved_template_revision"] == APPROVED_TEMPLATE_REVISION


def test_approved_template_sync_preserves_manual_published_version(client, db_session_factory, caplog):
    with db_session_factory() as db:
        seed_dictionaries(db)
        services = seed_services(db, seed_categories(db))
        service = services[("ГИА: Администрирование", "Заказ воды")]
        manual = ServiceDeskTemplateVersion(
            service_id=service.id,
            version=1,
            status=TemplateVersionStatus.PUBLISHED,
            system_settings={"default_title": "Ручная форма"},
        )
        db.add(manual)
        db.flush()
        seed_templates(db, services)
        db.commit()

        versions = list(
            db.scalars(
                select(ServiceDeskTemplateVersion)
                .where(ServiceDeskTemplateVersion.service_id == service.id)
                .order_by(ServiceDeskTemplateVersion.version)
            )
        )
        assert versions[0].status == TemplateVersionStatus.PUBLISHED
        assert versions[0].system_settings == {"default_title": "Ручная форма"}
        assert versions[1].status == TemplateVersionStatus.DRAFT
        assert versions[1].system_settings["_approved_template_revision"] == APPROVED_TEMPLATE_REVISION
    assert "approved_template_manual_conflict" in caplog.text
