import uuid
from datetime import UTC, date, datetime

from app.core.database import SessionLocal
from app.core.enums import (
    ProjectMemberRole,
    ProjectPriority,
    ProjectResponseStatus,
    ProjectStatus,
    ProjectType,
    UserRole,
)
from app.modules.projects.models import Project, ProjectMember
from app.modules.responses.models import ProjectResponse
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


DEMO_IDENTITY_USER_IDS = {
    "admin@utmn.ru": uuid.UUID("00000000-0000-0000-0000-000000000001"),
    "manager@utmn.ru": uuid.UUID("00000000-0000-0000-0000-000000000002"),
    "employee@utmn.ru": uuid.UUID("00000000-0000-0000-0000-000000000003"),
    "analyst@utmn.ru": uuid.UUID("00000000-0000-0000-0000-000000000004"),
}


def upsert_user(
    repo: UserRepository,
    *,
    email: str,
    full_name: str,
    role: UserRole,
    user_id: uuid.UUID | None = None,
    department: str | None = None,
    position: str | None = None,
    competencies: str | None = None,
    about: str | None = None,
) -> User:
    user = repo.get_by_email(email)
    if user is not None:
        user.full_name = full_name
        user.role = role
        user.department = department
        user.position = position
        user.competencies = competencies
        user.about = about
        return user
    return repo.create(
        user_id=user_id,
        email=email,
        full_name=full_name,
        role=role,
        department=department,
        position=position,
        competencies=competencies,
        about=about,
    )


def competency_blocks(*items: tuple[str, list[str]]) -> list[dict]:
    return [{"title": title, "competencies": competencies} for title, competencies in items]


def refresh_demo_project_competencies(db) -> None:
    demo_competencies = {
        "Цифровая карта образовательных инициатив": competency_blocks(
            ("Аналитика и данные", ["Аналитика данных", "SQL", "Визуализация данных"]),
            ("Исследование пользователей", ["Интервью"]),
        ),
        "Наставничество для новых преподавателей": competency_blocks(
            ("Методология", ["Методология образования", "Наставничество"]),
            ("Коммуникация", ["Коммуникации", "Фасилитация"]),
        ),
        "Исследование вовлечённости сотрудников": competency_blocks(
            ("Полевое исследование", ["Опросы", "Интервью"]),
            ("Аналитика", ["Аналитика данных"]),
        ),
    }
    for title, blocks in demo_competencies.items():
        project = db.query(Project).filter(Project.title == title).one_or_none()
        if project is not None:
            project.competency_blocks = blocks
            project.required_competencies = ", ".join(
                competency for block in blocks for competency in block["competencies"]
            )


def main() -> None:
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        admin = upsert_user(
            repo,
            email="admin@utmn.ru",
            user_id=DEMO_IDENTITY_USER_IDS["admin@utmn.ru"],
            full_name="Администратор ШПИУ",
            role=UserRole.ADMIN,
            department="ШПИУ",
            position="Администратор витрины",
        )
        manager = upsert_user(
            repo,
            email="manager@utmn.ru",
            user_id=DEMO_IDENTITY_USER_IDS["manager@utmn.ru"],
            full_name="Руководитель проекта",
            role=UserRole.PROJECT_MANAGER,
            department="ШПИУ",
            position="Руководитель проектных инициатив",
            competencies="Управление проектами, Коммуникации, Фасилитация, Наставничество",
            about="Ведёт проектные инициативы и собирает рабочие группы под задачи ШПИУ.",
        )
        employee = upsert_user(
            repo,
            email="employee@utmn.ru",
            user_id=DEMO_IDENTITY_USER_IDS["employee@utmn.ru"],
            full_name="Сотрудник ШПИУ",
            role=UserRole.EMPLOYEE,
            department="ШПИУ",
            position="Методист проектных программ",
            competencies="Коммуникации, Русский язык, Наставничество, Организация встреч",
            about="Помогает с коммуникациями, методическими материалами и сопровождением участников.",
        )
        analyst = upsert_user(
            repo,
            email="analyst@utmn.ru",
            user_id=DEMO_IDENTITY_USER_IDS["analyst@utmn.ru"],
            full_name="Аналитик ШПИУ",
            role=UserRole.EMPLOYEE,
            department="Аналитика",
            position="Аналитик данных",
            competencies="SQL, Аналитика данных, Интервью, Визуализация данных",
            about="Собирает данные, проводит интервью и готовит аналитические выводы.",
        )

        if db.query(Project).count() == 0:
            projects = [
                Project(
                    title="Цифровая карта образовательных инициатив",
                    short_description="Единая карта инициатив для руководителей и проектных команд.",
                    description="Проект собирает образовательные инициативы ШПИУ в единую витрину с ответственными, сроками и ожидаемыми результатами.",
                    goal="Повысить прозрачность проектной деятельности и упростить приоритизацию инициатив.",
                    expected_result="Руководство видит актуальный портфель инициатив и точки перегрузки.",
                    project_type=ProjectType.STRATEGIC,
                    priority=ProjectPriority.CRITICAL,
                    status=ProjectStatus.ACTIVE,
                    start_date=date(2026, 9, 1),
                    responsible_user_id=manager.id,
                    contact_email="manager@utmn.ru",
                    required_competencies="Аналитика данных, SQL, Интервью, Визуализация данных",
                    competency_blocks=competency_blocks(
                        ("Аналитика и данные", ["Аналитика данных", "SQL", "Визуализация данных"]),
                        ("Исследование пользователей", ["Интервью"]),
                    ),
                    planned_tasks="Собрать требования, описать данные, подготовить витрину",
                    created_by=admin.id,
                ),
                Project(
                    title="Наставничество для новых преподавателей",
                    short_description="Программа сопровождения новых преподавателей в первые месяцы работы.",
                    description="Команда проектирует маршрут адаптации, материалы и точки обратной связи для новых преподавателей.",
                    goal="Снизить время адаптации и повысить качество включения в образовательные процессы.",
                    expected_result="Готовый маршрут наставничества и пилотная группа участников.",
                    project_type=ProjectType.STRATEGIC,
                    priority=ProjectPriority.HIGH,
                    status=ProjectStatus.ACTIVE,
                    responsible_user_id=manager.id,
                    contact_email="manager@utmn.ru",
                    required_competencies="Методология образования, Коммуникации, Фасилитация, Наставничество",
                    competency_blocks=competency_blocks(
                        ("Методология", ["Методология образования", "Наставничество"]),
                        ("Коммуникация", ["Коммуникации", "Фасилитация"]),
                    ),
                    planned_tasks="Описать маршрут, собрать наставников, провести пилот",
                    created_by=admin.id,
                ),
                Project(
                    title="Исследование вовлечённости сотрудников",
                    short_description="Быстрое исследование барьеров участия сотрудников в проектах.",
                    description="Проект проверяет, почему сотрудники редко откликаются на инициативы и какие форматы вовлечения работают лучше.",
                    goal="Найти практические меры для роста вовлечённости в проектную деятельность.",
                    expected_result="Отчёт с гипотезами, сегментами и рекомендациями.",
                    project_type=ProjectType.STRATEGIC,
                    priority=ProjectPriority.HIGH,
                    status=ProjectStatus.ACTIVE,
                    start_date=date(2026, 10, 1),
                    end_date=date(2026, 12, 15),
                    responsible_user_id=analyst.id,
                    contact_email="analyst@utmn.ru",
                    required_competencies="Опросы, Интервью, Аналитика данных",
                    competency_blocks=competency_blocks(
                        ("Полевое исследование", ["Опросы", "Интервью"]),
                        ("Аналитика", ["Аналитика данных"]),
                    ),
                    planned_tasks="Подготовить анкету, провести интервью, собрать выводы",
                    created_by=admin.id,
                ),
                Project(
                    title="Календарь проектных событий",
                    short_description="Общий календарь встреч, защит и рабочих сессий.",
                    description="Проект временно приостановлен до согласования формата календаря и владельца процесса.",
                    goal="Сделать проектные события предсказуемыми и доступными для сотрудников.",
                    expected_result="Пилот календаря с ответственными и регулярными обновлениями.",
                    project_type=ProjectType.STRATEGIC,
                    priority=ProjectPriority.MEDIUM,
                    status=ProjectStatus.PAUSED,
                    created_by=admin.id,
                ),
                Project(
                    title="Архив проектных практик 2025",
                    short_description="Собранные кейсы завершённых проектных практик.",
                    description="Команда собрала и структурировала практики, которые можно переиспользовать в новых инициативах.",
                    goal="Сохранить проектную память и ускорить запуск похожих инициатив.",
                    expected_result="Каталог практик и краткие карточки кейсов.",
                    project_type=ProjectType.STRATEGIC,
                    priority=ProjectPriority.LOW,
                    status=ProjectStatus.COMPLETED,
                    end_date=date(2026, 5, 30),
                    created_by=admin.id,
                ),
                Project(
                    title="Старая витрина проектных заявок",
                    short_description="Архивная версия витрины для проверки soft archive.",
                    description="Архивный проект не должен отображаться в публичной витрине.",
                    goal="Проверить работу архивирования.",
                    project_type=ProjectType.STRATEGIC,
                    priority=ProjectPriority.LOW,
                    status=ProjectStatus.ARCHIVED,
                    archived_at=datetime.now(UTC),
                    created_by=admin.id,
                ),
            ]
            db.add_all(projects)
            db.flush()
            db.add_all(
                [
                    ProjectMember(project_id=projects[0].id, user_id=manager.id, member_role=ProjectMemberRole.MANAGER),
                    ProjectMember(
                        project_id=projects[0].id,
                        user_id=analyst.id,
                        member_role=ProjectMemberRole.WORKING_GROUP_MEMBER,
                    ),
                    ProjectMember(
                        project_id=projects[1].id,
                        user_id=employee.id,
                        member_role=ProjectMemberRole.PARTICIPANT,
                    ),
                    ProjectResponse(
                        project_id=projects[0].id,
                        user_id=employee.id,
                        full_name=employee.full_name,
                        email=employee.email,
                        comment="Хочу помочь с описанием процессов и сбором обратной связи.",
                        competencies="Коммуникации, организация встреч",
                        status=ProjectResponseStatus.NEW,
                    ),
                    ProjectResponse(
                        project_id=projects[0].id,
                        user_id=analyst.id,
                        full_name=analyst.full_name,
                        email=analyst.email,
                        comment="Готов подключиться к аналитике и структуре данных.",
                        competencies="SQL, аналитика, визуализация",
                        status=ProjectResponseStatus.CONTACTED,
                        processed_by=admin.id,
                        processed_at=datetime.now(UTC),
                    ),
                    ProjectResponse(
                        project_id=projects[1].id,
                        user_id=employee.id,
                        full_name=employee.full_name,
                        email=employee.email,
                        comment="Интересна методическая часть и сопровождение новичков.",
                        competencies="Методология, наставничество",
                        status=ProjectResponseStatus.ACCEPTED,
                        processed_by=admin.id,
                        processed_at=datetime.now(UTC),
                    ),
                    ProjectResponse(
                        project_id=projects[2].id,
                        user_id=analyst.id,
                        full_name=analyst.full_name,
                        email=analyst.email,
                        comment="Могу провести интервью и обработать результаты.",
                        competencies="Интервью, анализ качественных данных",
                        status=ProjectResponseStatus.VIEWED,
                        processed_by=admin.id,
                        processed_at=datetime.now(UTC),
                    ),
                    ProjectResponse(
                        project_id=projects[3].id,
                        user_id=employee.id,
                        full_name=employee.full_name,
                        email=employee.email,
                        comment="Сейчас не смогу участвовать регулярно.",
                        competencies="Координация",
                        status=ProjectResponseStatus.REJECTED,
                        processed_by=admin.id,
                        processed_at=datetime.now(UTC),
                    ),
                ]
            )

        refresh_demo_project_competencies(db)
        db.commit()
        print("Seed data is ready")
    finally:
        db.close()


if __name__ == "__main__":
    main()
