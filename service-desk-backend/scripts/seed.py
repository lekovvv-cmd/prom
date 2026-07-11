from __future__ import annotations

import sys
import uuid
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, or_, select, text
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import SessionLocal, utc_now  # noqa: E402
from app.core.enums import (  # noqa: E402
    ServiceDeskAccessType,
    TemplateFieldType,
    TemplateVersionStatus,
)
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability  # noqa: E402
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService  # noqa: E402
from app.modules.templates.models import (  # noqa: E402
    ServiceDeskDictionary,
    ServiceDeskDictionaryItem,
    ServiceDeskTemplateField,
    ServiceDeskTemplateVersion,
)
from app.modules.templates.schemas import DEFAULT_SYSTEM_SETTINGS  # noqa: E402


ROOT_CATEGORIES = [
    "Сопровождение учебного процесса",
    "Административно-хозяйственное сопровождение",
    "ГИА: Администрирование",
    "ГИА: Работа с обучающимися",
    "Практика: Организация и договоры",
    "Практика: Сопровождение",
]

DEMO_SERVICE_DESK_USERS = (
    {
        "identity_user_id": "00000000-0000-0000-0000-000000000001",
        "email": "admin@utmn.ru",
        "display_name": "Администратор ШПИУ",
        "department": "ШПИУ",
        "position": "Администратор Service Desk",
        "access_type": ServiceDeskAccessType.SERVICE_DESK_ADMIN,
        "capabilities": (),
    },
    {
        "identity_user_id": "00000000-0000-0000-0000-000000000002",
        "email": "manager@utmn.ru",
        "display_name": "Руководитель проекта",
        "department": "ШПИУ",
        "position": "Руководитель проектных инициатив",
        "access_type": ServiceDeskAccessType.MANAGER,
        "capabilities": (
            "service_desk.access",
            "service_desk.create_request",
            "service_desk.approve",
            "service_desk.assign",
            "service_desk.view_reports",
            "service_desk.manage_catalog",
            "service_desk.manage_templates",
            "service_desk.manage_approval_workflows",
            "service_desk.manage_sla",
        ),
    },
    {
        "identity_user_id": "00000000-0000-0000-0000-000000000003",
        "email": "employee@utmn.ru",
        "display_name": "Сотрудник ШПИУ",
        "department": "ШПИУ",
        "position": "Методист проектных программ",
        "access_type": ServiceDeskAccessType.MANAGER,
        "capabilities": (
            "service_desk.access",
            "service_desk.be_assignee",
        ),
    },
    {
        "identity_user_id": "00000000-0000-0000-0000-000000000004",
        "email": "analyst@utmn.ru",
        "display_name": "Аналитик ШПИУ",
        "department": "Аналитика",
        "position": "Аналитик данных",
        "access_type": ServiceDeskAccessType.MANAGER,
        "capabilities": (
            "service_desk.access",
            "service_desk.create_request",
            "service_desk.be_assignee",
        ),
    },
)

SERVICES_BY_CATEGORY = {
    "Сопровождение учебного процесса": [
        "Перенос занятий, замена преподавателя",
        "Обеспечение подписания индивидуальных планов преподавателей",
        "Ознакомление ППС с приказами",
        "Составление графика консультаций",
        "Составление перечня дисциплин и списка ППС школы",
        "Бронирование аудиторий",
        "Трудоустройство выпускников",
    ],
    "Административно-хозяйственное сопровождение": [
        "Бронирование аудиторий",
        "На печать в Издательство",
        "Роль табельщика",
        "Ввоз/вывоз и внос/вынос материальных ценностей",
        "Допуск в здание",
        "Оформление и регистрация исходящего документа",
        "Транспортное обслуживание",
        "Получение со склада",
        "Заказ сувенирной продукции",
        "График отпусков",
    ],
    "ГИА: Администрирование": [
        "Заказ воды",
        "Установка камер",
        "Запуск проекта приказа о составе ГЭК",
        "Запуск договора с председателем/членом ГЭК",
        "Подготовка обоснования цены договора",
        "Создание представления на допуск в здание членов ГЭК",
        "Подготовка приказа об организации и проведении ГИА по ОП ВО",
        "Подготовка приказа о подготовке отчёта «Итоги ГИА»",
    ],
    "ГИА: Работа с обучающимися": [
        "Подготовка приказа о распределении студентов по группам для проведения ГИА",
        "Подготовка приказа о предоставлении ВКР в ГЭК",
        "Подготовка приказа о подготовке и оформлении билетов к заседанию ГЭК",
        "Рассылка информационных материалов студентам",
        "Организация встречи со студентами",
    ],
    "Практика: Организация и договоры": [
        "Сопровождение практики",
        "Подготовка приказа о направлении на практику",
        "Заключение договора о практической подготовке",
        "Подготовка ИУП/ИКУГ",
        "Внесение изменений в приказ",
    ],
    "Практика: Сопровождение": [
        "Изменение сроков прохождения практики",
        "Подготовка представления на практику",
        "Подготовка отчёта руководителя практик",
        "Размещение отчётов на файловых ресурсах",
        "Организация встречи со студентами",
        "Подготовка материалов",
    ],
}

DICTIONARIES = {
    "building_addresses": {
        "title": "Адреса корпусов",
        "items": [
            ("Ленина 38", "lenina_38"),
            ("Ленина 16", "lenina_16"),
            ("Ленина 23", "lenina_23"),
            ("Перекопская 15", "perekopskaya_15"),
            ("Республика 9", "respubliki_9"),
            ("Другое", "other"),
        ],
    },
    "water_type": {
        "title": "Тип воды",
        "items": [
            ("Газированная", "sparkling"),
            ("Негазированная", "still"),
            ("Другое", "other"),
        ],
    },
    "gia_type": {
        "title": "Вид ГИА",
        "items": [
            ("Государственный экзамен", "state_exam"),
            ("ВКР", "vkr"),
        ],
    },
    "movement_type": {
        "title": "Тип перемещения материальных ценностей",
        "items": [
            ("Ввоз", "import"),
            ("Вывоз", "export"),
            ("Внос", "bring_in"),
            ("Вынос", "take_out"),
        ],
    },
}

def field(
    key: str,
    label: str,
    field_type: TemplateFieldType,
    position: int,
    *,
    is_required: bool = True,
    placeholder: str | None = None,
    dictionary_code: str | None = None,
    validation: dict[str, Any] | None = None,
    visibility_rules: dict[str, Any] | None = None,
    required_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "field_type": field_type,
        "position": position,
        "is_required": is_required,
        "placeholder": placeholder,
        "dictionary_code": dictionary_code,
        "validation": validation,
        "visibility_rules": visibility_rules,
        "required_rules": required_rules,
    }


TEMPLATE_FIELDS = {
    "Бронирование аудиторий": [
        field("building_address", "Адрес корпуса", TemplateFieldType.SELECT, 0, dictionary_code="building_addresses"),
        field("room_number", "Номер аудитории", TemplateFieldType.TEXT, 1, placeholder="Например: 305"),
        field("starts_at", "Дата и время начала", TemplateFieldType.DATETIME, 2),
        field("ends_at", "Дата и время окончания", TemplateFieldType.DATETIME, 3),
        field("participants_count", "Количество участников", TemplateFieldType.NUMBER, 4, validation={"min": 1}),
    ],
    "Перенос занятий, замена преподавателя": [
        field("discipline", "Дисциплина", TemplateFieldType.TEXT, 0),
        field("current_datetime", "Текущая дата и время занятия", TemplateFieldType.DATETIME, 1),
        field("new_datetime", "Новая дата и время занятия", TemplateFieldType.DATETIME, 2),
        field("requires_substitute_teacher", "Нужен заменяющий преподаватель", TemplateFieldType.CHECKBOX, 3),
        field(
            "substitute_teacher_full_name",
            "ФИО заменяющего преподавателя",
            TemplateFieldType.TEXT,
            4,
            is_required=False,
            visibility_rules={"field": "requires_substitute_teacher", "operator": "equals", "value": True},
            required_rules={"field": "requires_substitute_teacher", "operator": "equals", "value": True},
        ),
    ],
    "Ввоз/вывоз и внос/вынос материальных ценностей": [
        field("movement_type", "Тип перемещения", TemplateFieldType.SELECT, 0, dictionary_code="movement_type"),
        field("material_description", "Описание материальных ценностей", TemplateFieldType.TEXTAREA, 1),
        field("responsible_person", "Ответственный", TemplateFieldType.TEXT, 2),
        field("movement_date", "Дата перемещения", TemplateFieldType.DATE, 3),
    ],
    "Допуск в здание": [
        field("visitor_full_name", "ФИО посетителя", TemplateFieldType.TEXT, 0),
        field("organization", "Организация", TemplateFieldType.TEXT, 1, is_required=False),
        field("building_address", "Адрес корпуса", TemplateFieldType.SELECT, 2, dictionary_code="building_addresses"),
        field("access_date", "Дата допуска", TemplateFieldType.DATE, 3),
    ],
    "Заказ воды": [
        field("gia_type", "Вид ГИА", TemplateFieldType.SELECT, 0, dictionary_code="gia_type"),
        field("water_type", "Тип воды", TemplateFieldType.SELECT, 1, dictionary_code="water_type"),
        field("bottle_count", "Количество бутылок", TemplateFieldType.NUMBER, 2, validation={"min": 1, "max": 500}),
        field("delivery_date", "Дата доставки", TemplateFieldType.DATE, 3),
    ],
    "Подготовка приказа о направлении на практику": [
        field("direction", "Направление подготовки", TemplateFieldType.TEXT, 0),
        field("course", "Курс", TemplateFieldType.NUMBER, 1, validation={"min": 1, "max": 6}),
        field("group_name", "Учебная группа", TemplateFieldType.TEXT, 2),
        field("practice_start", "Дата начала практики", TemplateFieldType.DATE, 3),
        field("practice_end", "Дата окончания практики", TemplateFieldType.DATE, 4),
        field("comment", "Комментарий", TemplateFieldType.TEXTAREA, 5, is_required=False),
    ],
}


def main(session_factory: Callable[[], Session] | sessionmaker[Session] = SessionLocal) -> None:
    with session_factory() as db:
        seed_service_desk_users(db)
        seed_dictionaries(db)
        categories = seed_categories(db)
        services = seed_services(db, categories)
        seed_templates(db, services)
        db.commit()


def resolve_demo_identity_user_ids() -> dict[str, str]:
    values = {payload["email"]: payload["identity_user_id"] for payload in DEMO_SERVICE_DESK_USERS}
    identity_database_url = os.getenv("SERVICE_DESK_IDENTITY_DATABASE_URL")
    if not identity_database_url:
        return values

    try:
        engine = create_engine(identity_database_url)
        with engine.connect() as connection:
            rows = connection.execute(
                text("select id::text as id, email from users where email = any(:emails)"),
                {"emails": list(values)},
            ).mappings()
            for row in rows:
                values[row["email"]] = row["id"]
    except Exception as exc:  # pragma: no cover - local dev helper fallback
        print(f"[seed] Could not sync Service Desk identity users: {exc}", file=sys.stderr)
    return values


def seed_service_desk_users(db: Session) -> None:
    identity_user_ids = resolve_demo_identity_user_ids()
    for payload in DEMO_SERVICE_DESK_USERS:
        identity_user_id = identity_user_ids[payload["email"]]
        user = db.scalar(
            select(ServiceDeskUser).where(
                or_(
                    ServiceDeskUser.identity_user_id == identity_user_id,
                    ServiceDeskUser.email == payload["email"],
                )
            )
        )
        if not user:
            user = ServiceDeskUser(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"prom:{payload['identity_user_id']}"),
                identity_user_id=identity_user_id,
                email=payload["email"],
                display_name=payload["display_name"],
                department=payload["department"],
                position=payload["position"],
                access_type=payload["access_type"],
            )
            db.add(user)
            db.flush()
        else:
            user.identity_user_id = identity_user_id
            user.email = payload["email"]
            user.display_name = payload["display_name"]
            user.department = payload["department"]
            user.position = payload["position"]
            user.access_type = payload["access_type"]
            user.is_active = True

        existing_capabilities = {item.capability for item in user.capabilities}
        for capability in payload["capabilities"]:
            if capability not in existing_capabilities:
                db.add(
                    ServiceDeskUserCapability(
                        service_desk_user_id=user.id,
                        capability=capability,
                    )
                )


def seed_dictionaries(db: Session) -> None:
    for code, payload in DICTIONARIES.items():
        dictionary = db.scalar(select(ServiceDeskDictionary).where(ServiceDeskDictionary.code == code))
        if not dictionary:
            dictionary = ServiceDeskDictionary(code=code, title=payload["title"])
            db.add(dictionary)
            db.flush()

        existing_values = {
            item.value
            for item in db.scalars(
                select(ServiceDeskDictionaryItem).where(ServiceDeskDictionaryItem.dictionary_id == dictionary.id)
            )
        }
        for position, (label, value) in enumerate(payload["items"]):
            if value in existing_values:
                continue
            db.add(
                ServiceDeskDictionaryItem(
                    dictionary_id=dictionary.id,
                    label=label,
                    value=value,
                    position=position,
                    metadata_json={},
                )
            )


def seed_categories(db: Session) -> dict[str, ServiceDeskCategory]:
    categories: dict[str, ServiceDeskCategory] = {}
    for position, title in enumerate(ROOT_CATEGORIES):
        category = db.scalar(
            select(ServiceDeskCategory).where(
                ServiceDeskCategory.title == title,
                ServiceDeskCategory.parent_id.is_(None),
            )
        )
        if not category:
            category = ServiceDeskCategory(title=title, position=position)
            db.add(category)
            db.flush()
        categories[title] = category
    return categories


def seed_services(
    db: Session,
    categories: dict[str, ServiceDeskCategory],
) -> dict[str, ServiceDeskService]:
    services: dict[str, ServiceDeskService] = {}
    for category_title, service_titles in SERVICES_BY_CATEGORY.items():
        category = categories[category_title]
        for position, title in enumerate(service_titles):
            service = db.scalar(
                select(ServiceDeskService).where(
                    ServiceDeskService.category_id == category.id,
                    ServiceDeskService.title == title,
                )
            )
            if not service:
                service = ServiceDeskService(
                    category_id=category.id,
                    title=title,
                    short_description=f"Заявка: {title}.",
                    position=position,
                )
                db.add(service)
                db.flush()
            services[title] = service
    return services


def seed_templates(
    db: Session,
    services: dict[str, ServiceDeskService],
) -> None:
    for service_title, fields in TEMPLATE_FIELDS.items():
        service = services.get(service_title)
        if not service:
            continue
        existing = db.scalar(
            select(ServiceDeskTemplateVersion).where(ServiceDeskTemplateVersion.service_id == service.id)
        )
        if existing:
            continue

        now = utc_now()
        version = ServiceDeskTemplateVersion(
            service_id=service.id,
            version=1,
            status=TemplateVersionStatus.PUBLISHED,
            system_settings={
                **DEFAULT_SYSTEM_SETTINGS,
                "default_title": service.title,
                "help_text": "Заполните поля формы и приложите файлы при необходимости.",
            },
            published_at=now,
        )
        db.add(version)
        db.flush()
        for payload in fields:
            db.add(ServiceDeskTemplateField(template_version_id=version.id, **payload))


if __name__ == "__main__":
    main()
