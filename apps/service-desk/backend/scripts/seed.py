from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import SessionLocal, utc_now  # noqa: E402
from app.core.enums import (  # noqa: E402
    TemplateFieldType,
    TemplateVersionStatus,
)
from app.modules.access import models as access_models  # noqa: E402, F401
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


class DictionarySeed(TypedDict):
    title: str
    items: list[tuple[str, str]]

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
        "Роль табельщика (табель рабочего времени, график отпусков)",
        "Ввоз (вывоз) и внос (вынос) материальных ценностей",
        "Допуск в здание",
        "Оформление и регистрация исходящего документа",
        "Транспортное обслуживание",
        "Получение со склада (кроме компьютерной техники)",
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

APPROVED_TEMPLATE_REVISION = "approved-11-v1"
APPROVED_TEMPLATE_SOURCE = "PROM_TZ_11_APPROVED_SERVICE_DESK_TEMPLATES.md"
APPROVED_TEMPLATE_REVISION_BY_SERVICE = {
    "Установка камер": "approved-11-v3-remove-installation-address",
    "Ввоз (вывоз) и внос (вынос) материальных ценностей": "approved-11-v2-dictionaries",
}

OBSOLETE_DICTIONARY_REPLACEMENTS = {
    "camera_installation_addresses": "building_addresses",
}

SEED_TEMPLATE_REVISION_BY_SERVICE = {
    "Перенос занятий, замена преподавателя": "seed-v4-unified-datetime-change",
}

logger = logging.getLogger(__name__)

APPROVED_SERVICE_ALIASES = {
    "Оформление и регистрация исходящего документа": ("Регистрация исходящего документа",),
    "Получение со склада (кроме компьютерной техники)": (
        "Получение со склада (не компьютерная техника)",
        "Получение со склада",
    ),
    "Ввоз (вывоз) и внос (вынос) материальных ценностей": ("Ввоз/вывоз и внос/вынос материальных ценностей",),
    "Заказ воды": ("Заказ воды (ГИА)",),
    "Установка камер": ("Установка камер (ГИА)",),
    "Роль табельщика (табель рабочего времени, график отпусков)": ("Роль табельщика",),
}

APPROVED_TEMPLATE_CATEGORY_BY_SERVICE = {
    "Заказ воды": "ГИА: Администрирование",
    "Установка камер": "ГИА: Администрирование",
    "Бронирование аудиторий": "Административно-хозяйственное сопровождение",
    "На печать в Издательство": "Административно-хозяйственное сопровождение",
    "Роль табельщика (табель рабочего времени, график отпусков)": "Административно-хозяйственное сопровождение",
    "Ввоз (вывоз) и внос (вынос) материальных ценностей": "Административно-хозяйственное сопровождение",
    "Допуск в здание": "Административно-хозяйственное сопровождение",
    "Транспортное обслуживание": "Административно-хозяйственное сопровождение",
    "Оформление и регистрация исходящего документа": "Административно-хозяйственное сопровождение",
    "График отпусков": "Административно-хозяйственное сопровождение",
    "Получение со склада (кроме компьютерной техники)": "Административно-хозяйственное сопровождение",
}

DICTIONARIES: dict[str, DictionarySeed] = {
    "building_addresses": {
        "title": "Адреса корпусов",
        "items": [
            ("Ленина 16", "lenina_16"),
            ("Ленина 23", "lenina_23"),
            ("Ленина 38", "lenina_38"),
            ("Перекопская 15", "perekopskaya_15"),
            ("Республики 9", "respubliki_9"),
            ("Другое (укажите в комментарии)", "other"),
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
    "movement_type": {
        "title": "Тип перемещения материальных ценностей",
        "items": [
            ("Ввоз", "import"),
            ("Вывоз", "export"),
            ("Внос", "bring_in"),
            ("Вынос", "take_out"),
        ],
    },
    "gia_type": {
        "title": "Вид ГИА",
        "items": [
            ("гос.экзамен", "state_exam"),
            ("ВКР", "vkr"),
        ],
    },
    "institutes": {"title": "Институты", "items": [("ШПИУ", "shpiu")]},
    "study_directions": {
        "title": "Направления подготовки (локальный набор)",
        "items": [
            ("38.03.04 Государственное и муниципальное управление", "38_03_04_gmu"),
            ("38.05.02 Таможенное дело", "38_05_02_customs"),
            ("40.03.01 Юриспруденция", "40_03_01_law"),
            ("40.04.01 Юриспруденция (Магистр права)", "40_04_01_law_master"),
            ("40.04.01 Юриспруденция (Судебная власть и уголовная юстиция)", "40_04_01_criminal_justice"),
            ("40.04.01 Юриспруденция (Частное право и разрешение споров)", "40_04_01_private_law"),
            ("40.05.01 Правовое обеспечение национальной безопасности", "40_05_01_national_security"),
            ("40.05.04 Судебная и прокурорская деятельность", "40_05_04_prosecution"),
        ],
    },
    "publisher_approval_status": {
        "title": "Согласование с издательством",
        "items": [
            ("Согласовано", "approved"),
            ("Не согласовано", "not_approved"),
        ],
    },
    "disciplines": {
        "title": "Дисциплины",
        "items": [
            ("Математика", "mathematics"),
            ("Информатика", "computer_science"),
            ("Экономика", "economics"),
            ("Иностранный язык", "foreign_language"),
            ("Физическая культура", "physical_education"),
        ],
    },
    "teachers": {
        "title": "Преподаватели",
        "items": [
            ("Иванова Анна Сергеевна", "ivanova_a_s"),
            ("Петров Дмитрий Алексеевич", "petrov_d_a"),
            ("Смирнова Елена Викторовна", "smirnova_e_v"),
            ("Кузнецов Максим Олегович", "kuznetsov_m_o"),
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
    help_text: str | None = None,
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
        "help_text": help_text,
        "placeholder": placeholder,
        "dictionary_code": dictionary_code,
        "validation": validation,
        "visibility_rules": visibility_rules,
        "required_rules": required_rules,
    }


APPROVED_TEMPLATE_FIELDS = {
    "Заказ воды": [
        field("bottle_count", "Количество бутылок", TemplateFieldType.NUMBER, 0, validation={"min": 1}),
        field("bottle_volume", "Объем бутылок", TemplateFieldType.TEXT, 1),
        field("water_type", "Тип воды", TemplateFieldType.SELECT, 2, dictionary_code="water_type"),
        field("event_starts_at", "Дата и время начала мероприятия", TemplateFieldType.DATETIME, 3),
        field("event_ends_at", "Дата и время окончания мероприятия", TemplateFieldType.DATETIME, 4),
        field("commission_members_count", "Количество членов комиссии", TemplateFieldType.NUMBER, 5, validation={"min": 1}),
        field("gia_sessions_count", "Количество заседаний ГЭК", TemplateFieldType.NUMBER, 6, validation={"min": 1}),
        field("graduating_students_count", "Количество выпускающихся студентов", TemplateFieldType.NUMBER, 7, validation={"min": 1}),
    ],
    "Установка камер": [
        field("institute", "Институт", TemplateFieldType.SELECT, 0, dictionary_code="institutes", validation={"default_value": "shpiu"}),
        field("gia_type", "Вид ГИА", TemplateFieldType.SELECT, 1, dictionary_code="gia_type"),
        field("study_direction", "Направление (специальность)", TemplateFieldType.SELECT, 2, dictionary_code="study_directions"),
        field("room_number", "Номер аудитории для установки камер", TemplateFieldType.TEXT, 3),
        field("event_starts_at", "Дата и время начала мероприятия", TemplateFieldType.DATETIME, 4),
        field("event_ends_at", "Дата и время окончания мероприятия", TemplateFieldType.DATETIME, 5),
        field("comment", "комментарии", TemplateFieldType.TEXTAREA, 6, is_required=False),
    ],
    "Бронирование аудиторий": [
        field("booking_purpose", "Цель брони аудитории", TemplateFieldType.TEXTAREA, 0),
        field("approved_with_full_name", "ФИО (с кем согласовано)", TemplateFieldType.TEXT, 1),
        field("building_address", "Адрес корпуса брони аудитории", TemplateFieldType.SELECT, 2, dictionary_code="building_addresses"),
        field("room_number", "Номер аудитории", TemplateFieldType.TEXT, 3),
        field("event_starts_at", "Дата и время начала мероприятия", TemplateFieldType.DATETIME, 4),
        field("event_ends_at", "Дата и время окончания мероприятия", TemplateFieldType.DATETIME, 5),
        field("comment", "Комментарий", TemplateFieldType.TEXTAREA, 6, is_required=False),
    ],
    "На печать в Издательство": [
        field("event_name", "Название мероприятия", TemplateFieldType.TEXT, 0),
        field("publisher_approval_status", "Согласовано/не согласовано с издательством", TemplateFieldType.SELECT, 1, dictionary_code="publisher_approval_status"),
        field("product_type", "Вид продукции", TemplateFieldType.TEXT, 2),
        field("production_due_date", "Сроки изготовления", TemplateFieldType.DATE, 3),
        field("product_quantity", "Количество продукции", TemplateFieldType.NUMBER, 4, validation={"min": 1}),
        field("template_link", "Ссылка на шаблон", TemplateFieldType.TEXT, 5),
        field("additional_characteristics", "Дополнительные характеристики", TemplateFieldType.TEXTAREA, 6, is_required=False),
    ],
    "Роль табельщика (табель рабочего времени, график отпусков)": [
        field("employee_full_name", "ФИО", TemplateFieldType.TEXT, 0),
        field("vacation_starts_on", "Дата начала отпуска", TemplateFieldType.DATE, 1),
        field("vacation_ends_on", "Дата окончания отпуска", TemplateFieldType.DATE, 2),
    ],
    "Ввоз (вывоз) и внос (вынос) материальных ценностей": [
        field("event_name", "Название мероприятия", TemplateFieldType.TEXT, 0),
        field("movement_type", "Тип перемещения", TemplateFieldType.SELECT, 1, dictionary_code="movement_type"),
        field("movement_starts_at", "Дата и время вноса (ввоза)", TemplateFieldType.DATETIME, 2),
        field("movement_ends_at", "Дата и время выноса (вывоза)", TemplateFieldType.DATETIME, 3),
        field("inventory_list_file", "Прикрепите файл с перечнем МЦ", TemplateFieldType.FILE, 4),
        field("material_type", "Вид материальных ценностей", TemplateFieldType.TEXT, 5),
        field("packaging", "Тара", TemplateFieldType.TEXT, 6),
        field("vehicle_details", "Номер, модель ТС при ввозе (вывозе)", TemplateFieldType.TEXT, 7),
    ],
    "Допуск в здание": [
        field("person_full_name", "ФИО (на кого оформляется допуск)", TemplateFieldType.TEXTAREA, 0),
        field("equipment", "Оборудование", TemplateFieldType.TEXTAREA, 1, is_required=False),
        field("address", "Адрес", TemplateFieldType.TEXT, 2),
        field("access_starts_on", "Дата начала доступа", TemplateFieldType.DATE, 3),
        field("access_ends_on", "Дата прекращения доступа", TemplateFieldType.DATE, 4),
    ],
    "Транспортное обслуживание": [
        field("event_name", "Название мероприятия", TemplateFieldType.TEXT, 0),
        field("people_count", "Количество человек (всего)", TemplateFieldType.NUMBER, 1, validation={"min": 1}),
        field("students_count", "Количество студентов", TemplateFieldType.NUMBER, 2, validation={"min": 1}),
        field("event_starts_at", "Дата и время начала мероприятия", TemplateFieldType.DATETIME, 3),
        field("event_ends_at", "Дата и время окончания мероприятия", TemplateFieldType.DATETIME, 4),
        field("route", "Маршрут (откуда-куда)", TemplateFieldType.TEXTAREA, 5),
    ],
    "Оформление и регистрация исходящего документа": [
        field("document", "Документ", TemplateFieldType.TEXT, 0),
        field("document_file", "Проект или скан документа", TemplateFieldType.FILE, 1, help_text="Приложите проект документа в формате Word либо скан подписанного документа."),
    ],
    "График отпусков": [
        field("employee_full_name", "ФИО", TemplateFieldType.TEXT, 0),
        field("vacation_starts_on", "Дата начала отпуска", TemplateFieldType.DATE, 1),
        field("vacation_ends_on", "Дата окончания отпуска", TemplateFieldType.DATE, 2),
    ],
    "Получение со склада (кроме компьютерной техники)": [
        field("materially_responsible_person", "Материально ответственное лицо ФИО", TemplateFieldType.TEXT, 0),
        field("position", "Должность", TemplateFieldType.TEXT, 1),
        field("event_name", "Мероприятие", TemplateFieldType.TEXT, 2),
        field("inventory_list_file", "Список для выдачи со склада", TemplateFieldType.FILE, 3, help_text="Укажите материально ответственное лицо и приложите список имущества или канцелярии для выдачи."),
    ],
}


TEMPLATE_FIELDS = {
    "Перенос занятий, замена преподавателя": [
        field(
            "discipline",
            "Дисциплина",
            TemplateFieldType.TEXT,
            0,
            dictionary_code="disciplines",
            help_text="Начните вводить название дисциплины и выберите подсказку из справочника.",
        ),
        field("current_datetime", "Текущая дата и время занятия", TemplateFieldType.DATETIME, 1),
        field(
            "change_datetime",
            "Изменить дату и время занятия",
            TemplateFieldType.CHECKBOX,
            2,
            is_required=False,
            help_text="Отметьте, если занятие переносится на другую дату или время.",
        ),
        field(
            "new_datetime",
            "Новая дата и время занятия",
            TemplateFieldType.DATETIME,
            3,
            is_required=False,
            help_text="Укажите новую дату и время вместе.",
            visibility_rules={"field": "change_datetime", "operator": "equals", "value": True},
            required_rules={"field": "change_datetime", "operator": "equals", "value": True},
        ),
        field(
            "requires_substitute_teacher",
            "Нужен заменяющий преподаватель",
            TemplateFieldType.CHECKBOX,
            4,
            is_required=False,
        ),
        field(
            "substitute_teacher_full_name",
            "ФИО заменяющего преподавателя",
            TemplateFieldType.TEXT,
            5,
            is_required=False,
            dictionary_code="teachers",
            help_text="Начните вводить ФИО и выберите преподавателя из справочника.",
            visibility_rules={"field": "requires_substitute_teacher", "operator": "equals", "value": True},
            required_rules={"field": "requires_substitute_teacher", "operator": "equals", "value": True},
        ),
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
        seed_dictionaries(db)
        categories = seed_categories(db)
        services = seed_services(db, categories)
        seed_templates(db, services)
        db.commit()


def seed_dictionaries(db: Session) -> None:
    for code, payload in DICTIONARIES.items():
        dictionary = db.scalar(select(ServiceDeskDictionary).where(ServiceDeskDictionary.code == code))
        if not dictionary:
            dictionary = ServiceDeskDictionary(code=code, title=payload["title"])
            db.add(dictionary)
            db.flush()
        else:
            dictionary.title = payload["title"]

        existing_by_value = {
            item.value: item
            for item in db.scalars(
                select(ServiceDeskDictionaryItem).where(ServiceDeskDictionaryItem.dictionary_id == dictionary.id)
            )
        }
        for position, (label, value) in enumerate(payload["items"]):
            existing = existing_by_value.get(value)
            if existing:
                existing.label = label
                existing.position = position
                existing.is_active = True
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
    _retire_redundant_dictionaries(db)


def _retire_redundant_dictionaries(db: Session) -> None:
    for obsolete_code, replacement_code in OBSOLETE_DICTIONARY_REPLACEMENTS.items():
        dictionary = db.scalar(
            select(ServiceDeskDictionary).where(ServiceDeskDictionary.code == obsolete_code)
        )
        if not dictionary:
            continue
        for field in db.scalars(
            select(ServiceDeskTemplateField).where(
                ServiceDeskTemplateField.dictionary_code == obsolete_code
            )
        ):
            field.dictionary_code = replacement_code
        db.delete(dictionary)


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
) -> dict[tuple[str, str], ServiceDeskService]:
    services: dict[tuple[str, str], ServiceDeskService] = {}
    for category_title, service_titles in SERVICES_BY_CATEGORY.items():
        category = categories[category_title]
        for position, title in enumerate(service_titles):
            service = _find_service_by_title_or_alias(db, category.id, title)
            if not service:
                service = ServiceDeskService(
                    category_id=category.id,
                    title=title,
                    short_description=f"Заявка: {title}.",
                    position=position,
                )
                db.add(service)
                db.flush()
            elif service.title != title:
                service.title = title
                service.short_description = f"Заявка: {title}."
            services[(category_title, title)] = service
    return services


def _normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())


def _find_service_by_title_or_alias(
    db: Session,
    category_id: Any,
    official_title: str,
) -> ServiceDeskService | None:
    candidates = (official_title, *APPROVED_SERVICE_ALIASES.get(official_title, ()))
    normalized_candidates = {_normalize_title(item) for item in candidates}
    services = list(
        db.scalars(select(ServiceDeskService).where(ServiceDeskService.category_id == category_id))
    )
    return next(
        (service for service in services if _normalize_title(service.title) == _normalize_title(official_title)),
        next(
            (service for service in services if _normalize_title(service.title) in normalized_candidates),
            None,
        ),
    )


def seed_templates(
    db: Session,
    services: dict[tuple[str, str], ServiceDeskService],
) -> None:
    for (category_title, service_title), service in services.items():
        versions = list(
            db.scalars(
                select(ServiceDeskTemplateVersion)
                .where(ServiceDeskTemplateVersion.service_id == service.id)
                .order_by(ServiceDeskTemplateVersion.version.desc())
            )
        )
        approved_fields = (
            APPROVED_TEMPLATE_FIELDS.get(service_title)
            if APPROVED_TEMPLATE_CATEGORY_BY_SERVICE.get(service_title) == category_title
            else None
        )
        if approved_fields is not None:
            _sync_approved_template(db, service, versions, approved_fields)
            continue

        published = next((item for item in versions if item.status == TemplateVersionStatus.PUBLISHED), None)
        revision = SEED_TEMPLATE_REVISION_BY_SERVICE.get(service_title)
        if published:
            should_refresh_seed = (
                revision is not None
                and published.system_settings.get("_seed_generated") is True
                and published.system_settings.get("_seed_template_revision") != revision
            )
            if not should_refresh_seed:
                continue
            published.status = TemplateVersionStatus.ARCHIVED
            published.archived_at = utc_now()
        now = utc_now()
        fields = TEMPLATE_FIELDS.get(service_title, [])
        seed_version = next(
            (
                item
                for item in versions
                if item.system_settings.get("_seed_generated") is True
                and (
                    revision is None
                    or item.system_settings.get("_seed_template_revision") == revision
                )
            ),
            None,
        )
        if seed_version and seed_version.status == TemplateVersionStatus.ARCHIVED:
            version = seed_version
            version.status = TemplateVersionStatus.PUBLISHED
            version.published_at = now
            version.archived_at = None
            continue
        version = ServiceDeskTemplateVersion(
            service_id=service.id,
            version=max((item.version for item in versions), default=0) + 1,
            status=TemplateVersionStatus.PUBLISHED,
            system_settings={
                **DEFAULT_SYSTEM_SETTINGS,
                "default_title": service.title,
                "help_text": "Заполните поля формы и приложите файлы при необходимости.",
                "_seed_generated": True,
                **({"_seed_template_revision": revision} if revision else {}),
            },
            published_at=now,
        )
        db.add(version)
        db.flush()
        for payload in fields:
            db.add(ServiceDeskTemplateField(template_version_id=version.id, **payload))


def _sync_approved_template(
    db: Session,
    service: ServiceDeskService,
    versions: list[ServiceDeskTemplateVersion],
    fields: list[dict[str, Any]],
) -> None:
    revision = APPROVED_TEMPLATE_REVISION_BY_SERVICE.get(
        service.title,
        APPROVED_TEMPLATE_REVISION,
    )
    approved_version = next(
        (
            item
            for item in versions
            if item.system_settings.get("_approved_template_revision")
            == revision
        ),
        None,
    )
    if approved_version:
        return

    published = next(
        (item for item in versions if item.status == TemplateVersionStatus.PUBLISHED),
        None,
    )
    should_publish = published is None or published.system_settings.get("_seed_generated") is True
    now = utc_now()
    if published and should_publish:
        published.status = TemplateVersionStatus.ARCHIVED
        published.archived_at = now
    elif published:
        logger.warning(
            "approved_template_manual_conflict service=%s version=%s; created approved draft",
            service.title,
            published.version,
        )

    version = ServiceDeskTemplateVersion(
        service_id=service.id,
        version=max((item.version for item in versions), default=0) + 1,
        status=TemplateVersionStatus.PUBLISHED if should_publish else TemplateVersionStatus.DRAFT,
        system_settings={
            **DEFAULT_SYSTEM_SETTINGS,
            "default_title": service.title,
            "help_text": "Заполните поля формы и приложите файлы при необходимости.",
            "_seed_generated": True,
            "_approved_template_revision": revision,
            "_approved_template_source": APPROVED_TEMPLATE_SOURCE,
        },
        published_at=now if should_publish else None,
    )
    db.add(version)
    db.flush()
    for payload in fields:
        db.add(ServiceDeskTemplateField(template_version_id=version.id, **payload))


if __name__ == "__main__":
    main()
