# 07_AGENT_PROMPT.md — основной промпт для агента

Скопируй этот файл в чат с кодинг-агентом, если нужно дать ему короткую, но полную задачу.

---

Реализуй fullstack MVP продукта «Витрина проектов ШПИУ».

Продукт нужен для внутренней витрины стратегических проектов: сотрудники и преподаватели видят проекты, открывают подробности и откликаются; администратор создаёт/редактирует/архивирует проекты и обрабатывает отклики.

Стек:
- backend: Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL;
- frontend: React latest stable, TypeScript;
- frontend обязательно по Feature-Sliced Design;
- backend обязательно разбить на `api`, `core`, `modules`.

Backend-правила:
- `api` — только FastAPI routes/dependencies, без бизнес-логики;
- `core` — общие сущности, DTO, enums, config, database, security, shared utils;
- `core` не может импортировать ничего из `modules`;
- `modules` — бизнес-модули, модели, репозитории, сервисы/use cases;
- `api` вызывает `modules`;
- `modules` может импортировать из `core`.

Frontend-правила:
- использовать FSD:
  - `app`;
  - `pages`;
  - `widgets`;
  - `features`;
  - `entities`;
  - `shared`;
- не смешивать API-запросы с UI без необходимости;
- типы сущностей хранить в `entities`;
- пользовательские действия хранить в `features`.

Роли:
- `employee`;
- `project_manager`;
- `admin`.

MVP-авторизация:
- через email `@utmn.ru`;
- предусмотреть endpoints:
  - `POST /api/auth/request-code`;
  - `POST /api/auth/verify-code`;
  - `GET /api/me`;
- в dev-режиме можно использовать код `000000`;
- вернуть JWT;
- admin routes требуют роль admin или project_manager, если это проще для MVP.

Сущности:
- users;
- projects;
- project_members;
- project_responses;
- project_tags;
- project_tag_links.

Проект должен иметь:
- title;
- short_description;
- description;
- goal;
- expected_result;
- project_type;
- priority;
- status;
- start_date nullable;
- end_date nullable;
- responsible_user_id nullable;
- contact_email nullable;
- required_competencies nullable;
- planned_tasks nullable;
- created_by;
- created_at;
- updated_at;
- archived_at nullable.

В MVP `project_type` пока только `strategic`, но enum/фильтр должны позволять добавить типы позже.

Статусы проекта:
- draft;
- active;
- paused;
- completed;
- archived.

Статусы отклика:
- new;
- viewed;
- contacted;
- accepted;
- rejected;
- cancelled.

Public API:
- `GET /api/projects`;
- `GET /api/projects/{project_id}`;
- `POST /api/projects/{project_id}/responses`.

Admin API:
- `GET /api/admin/projects`;
- `POST /api/admin/projects`;
- `PATCH /api/admin/projects/{project_id}`;
- `DELETE /api/admin/projects/{project_id}` — soft archive, не физическое удаление;
- `GET /api/admin/projects/{project_id}/responses`;
- `GET /api/admin/responses`;
- `PATCH /api/admin/responses/{response_id}`;
- `GET /api/admin/stats`.

Frontend pages:
- `/login`;
- `/projects`;
- `/projects/:projectId`;
- `/admin/projects`;
- `/admin/responses`;
- `/admin/stats`.

Витрина проектов:
- карточки проектов;
- поиск по названию;
- фильтр по статусу;
- фильтр по типу;
- сортировка по дате создания / приоритету.

Карточка проекта:
- название;
- краткое описание;
- цель;
- тип / уровень проекта;
- ответственный;
- статус;
- дата или период, если есть;
- количество откликов;
- кнопка «Подробнее»;
- кнопка «Откликнуться».

Страница проекта:
- полное описание;
- цель;
- ожидаемый результат;
- ответственный;
- рабочая группа;
- требуемые компетенции, если есть;
- предполагаемые задачи, если есть;
- сроки, если есть;
- статус;
- форма отклика.

Админка:
- таблица проектов;
- создание проекта;
- редактирование проекта;
- архивирование проекта;
- список откликов;
- фильтр по проекту;
- фильтр по статусу;
- изменение статуса отклика;
- базовая статистика.

Добавь:
- README;
- `.env.example`;
- alembic migrations;
- seed demo data;
- CORS для локального frontend;
- понятные ошибки API.

Реализацию делай итерациями:
1. каркас backend/frontend;
2. модели и миграции;
3. public projects API;
4. responses API;
5. auth;
6. admin projects;
7. admin responses;
8. stats;
9. frontend pages;
10. финальная проверка end-to-end.

Главный smoke test:
- admin входит через `admin@utmn.ru`;
- создаёт проект;
- сотрудник видит проект;
- сотрудник отправляет отклик;
- admin видит отклик;
- admin меняет статус отклика.
