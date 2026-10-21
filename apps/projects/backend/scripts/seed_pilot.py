from __future__ import annotations

import uuid

from app.core.database import SessionLocal
from app.core.enums import ProjectPriority, ProjectStatus, ProjectType, UserRole
from app.modules.projects.models import Project
from app.modules.users.repository import UserRepository

PILOT_USERS = [
    ("pilot.admin01@utmn.ru", "Администратор PROM 1", UserRole.PLATFORM_ADMIN, None),
    ("pilot.admin02@utmn.ru", "Администратор PROM 2", UserRole.PLATFORM_ADMIN, None),
    ("pilot.pm01@utmn.ru", "Менеджер проектов 1", UserRole.PROJECT_MANAGER, "Управление проектами, Коммуникации"),
    ("pilot.pm02@utmn.ru", "Менеджер проектов 2", UserRole.PROJECT_MANAGER, "Фасилитация, Исследования пользователей"),
    ("pilot.pm03@utmn.ru", "Менеджер проектов 3", UserRole.PROJECT_MANAGER, "Методология образования, Наставничество"),
    ("pilot.pm04@utmn.ru", "Менеджер проектов 4", UserRole.PROJECT_MANAGER, "Аналитика данных, SQL"),
    ("pilot.pm05@utmn.ru", "Менеджер проектов 5", UserRole.PROJECT_MANAGER, "Документооборот, Коммуникации"),
    ("pilot.employee01@utmn.ru", "Сотрудник 1", UserRole.EMPLOYEE, "Аналитика данных, SQL, Визуализация данных"),
    ("pilot.employee02@utmn.ru", "Сотрудник 2", UserRole.EMPLOYEE, "UX/UI, Исследования пользователей, Интервью"),
    ("pilot.employee03@utmn.ru", "Сотрудник 3", UserRole.EMPLOYEE, "Frontend, Backend"),
    ("pilot.employee04@utmn.ru", "Сотрудник 4", UserRole.EMPLOYEE, "Проектное управление, Коммуникации, Фасилитация"),
    ("pilot.employee05@utmn.ru", "Сотрудник 5", UserRole.EMPLOYEE, "Исследования пользователей, Интервью, Документооборот"),
]

PROJECTS = [
    {
        "title": "Карта образовательных инициатив",
        "short_description": "Собрать актуальную картину образовательных проектов и их связей.",
        "description": "Пилотная команда описывает инициативы, ответственных и ожидаемые результаты.",
        "goal": "Сделать портфель инициатив понятным для сотрудников и руководителей.",
        "expected_result": "Каталог инициатив с владельцами и приоритетами.",
        "priority": ProjectPriority.HIGH,
        "status": ProjectStatus.ACTIVE,
        "required_competencies": "Аналитика данных, SQL, Визуализация данных",
        "competency_blocks": [{"title": "Данные", "competencies": ["Аналитика данных", "SQL", "Визуализация данных"]}],
        "planned_tasks": "Определить поля, собрать примеры, проверить прототип",
        "manager": "pilot.pm01@utmn.ru",
    },
    {
        "title": "Исследование опыта студентов",
        "short_description": "Понять, как студенты находят и используют образовательные сервисы.",
        "description": "Команда собирает обратную связь через интервью и короткий опрос.",
        "goal": "Выявить основные барьеры и полезные сценарии.",
        "expected_result": "Краткий отчёт с приоритетными улучшениями.",
        "priority": ProjectPriority.MEDIUM,
        "status": ProjectStatus.ACTIVE,
        "required_competencies": "Исследования пользователей, Интервью, UX/UI",
        "competency_blocks": [{"title": "Исследования", "competencies": ["Исследования пользователей", "Интервью", "UX/UI"]}],
        "planned_tasks": "Подготовить вопросы, провести интервью, обобщить наблюдения",
        "manager": "pilot.pm02@utmn.ru",
    },
    {
        "title": "Прототип витрины проектных данных",
        "short_description": "Проверить понятный способ представления проектных данных.",
        "description": "Небольшая команда подготовит и проверит рабочий интерфейс прототипа.",
        "goal": "Проверить навигацию и основные пользовательские сценарии.",
        "expected_result": "Интерактивный прототип и список улучшений.",
        "priority": ProjectPriority.HIGH,
        "status": ProjectStatus.ACTIVE,
        "required_competencies": "Frontend, Backend, UX/UI",
        "competency_blocks": [{"title": "Разработка", "competencies": ["Frontend", "Backend", "UX/UI"]}],
        "planned_tasks": "Согласовать сценарии, собрать прототип, провести проверку",
        "manager": "pilot.pm03@utmn.ru",
    },
    {
        "title": "Методические материалы для команд",
        "short_description": "Подготовить компактный стартовый набор для проектных команд.",
        "description": "Проект собирает шаблоны и практические подсказки для запуска инициатив.",
        "goal": "Упростить старт и координацию межфункциональных команд.",
        "expected_result": "Набор материалов с проверенными примерами.",
        "priority": ProjectPriority.MEDIUM,
        "status": ProjectStatus.DRAFT,
        "required_competencies": "Проектное управление, Коммуникации, Документооборот",
        "competency_blocks": [{"title": "Организация", "competencies": ["Проектное управление", "Коммуникации", "Документооборот"]}],
        "planned_tasks": "Собрать потребности, подготовить черновики, получить обратную связь",
        "manager": "pilot.pm04@utmn.ru",
    },
]


def stable_user_id(email: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"prom:pilot:{email}")


def main() -> None:
    with SessionLocal() as db:
        repo = UserRepository(db)
        users = {}
        for email, name, role, competencies in PILOT_USERS:
            user = repo.get_by_email(email)
            if user is None:
                user = repo.create(
                    user_id=stable_user_id(email),
                    email=email,
                    full_name=name,
                    role=role,
                    department="ТюмГУ",
                    position=name,
                    competencies=competencies,
                    about="Тестовая учётная запись двухнедельного пилота PROM." if role != UserRole.PLATFORM_ADMIN else None,
                )
            users[email] = user
        admin = users["pilot.admin01@utmn.ru"]
        for item in PROJECTS:
            if db.query(Project.id).filter(Project.title == item["title"]).first():
                continue
            manager = users[item["manager"]]
            db.add(Project(
                **{key: value for key, value in item.items() if key != "manager"},
                project_type=ProjectType.STRATEGIC,
                responsible_user_id=manager.id,
                contact_email=manager.email,
                created_by=admin.id,
            ))
        db.commit()
    print("Synchronized 12 PROM pilot profiles and 4 sample projects")


if __name__ == "__main__":
    main()
