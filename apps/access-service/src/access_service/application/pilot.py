from __future__ import annotations

import uuid

PILOT_USERS = [
    ("pilot.admin01@utmn.ru", "Администратор PROM 1", "platform_admin"),
    ("pilot.admin02@utmn.ru", "Администратор PROM 2", "platform_admin"),
    ("pilot.pm01@utmn.ru", "Менеджер проектов 1", "project_manager"),
    ("pilot.pm02@utmn.ru", "Менеджер проектов 2", "project_manager"),
    ("pilot.pm03@utmn.ru", "Менеджер проектов 3", "project_manager"),
    ("pilot.pm04@utmn.ru", "Менеджер проектов 4", "project_manager"),
    ("pilot.pm05@utmn.ru", "Менеджер проектов 5", "project_manager"),
    ("pilot.employee01@utmn.ru", "Сотрудник 1", "employee"),
    ("pilot.employee02@utmn.ru", "Сотрудник 2", "employee"),
    ("pilot.employee03@utmn.ru", "Сотрудник 3", "employee"),
    ("pilot.employee04@utmn.ru", "Сотрудник 4", "employee"),
    ("pilot.employee05@utmn.ru", "Сотрудник 5", "employee"),
]


def stable_user_id(email: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"prom:pilot:{email}"))
