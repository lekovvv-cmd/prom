# 04_BACKEND_TASKS.md — задачи для backend

## Цель

Реализовать backend MVP на FastAPI с архитектурой:

```txt
backend/
  app/
    main.py
    api/
    core/
    modules/
  alembic/
  alembic.ini
  pyproject.toml
  .env.example
  README.md
```

## Рекомендуемая структура

```txt
backend/
  app/
    main.py

    api/
      __init__.py
      deps.py
      router.py
      routes/
        __init__.py
        auth.py
        projects.py
        admin_projects.py
        admin_responses.py
        admin_stats.py

    core/
      __init__.py
      config.py
      database.py
      security.py
      pagination.py
      exceptions.py
      enums.py
      schemas/
        __init__.py
        common.py

    modules/
      __init__.py

      users/
        __init__.py
        models.py
        schemas.py
        repository.py
        service.py

      projects/
        __init__.py
        models.py
        schemas.py
        repository.py
        service.py

      responses/
        __init__.py
        models.py
        schemas.py
        repository.py
        service.py

      stats/
        __init__.py
        schemas.py
        service.py

  alembic/
    versions/

  scripts/
    seed.py

  tests/
```

## Важное правило импортов

Разрешено:

```txt
api -> modules
api -> core
modules -> core
```

Запрещено:

```txt
core -> modules
core -> api
modules -> api
```

## Основные backend-задачи

### 1. Инициализация проекта

- создать backend-приложение;
- настроить `pyproject.toml`;
- добавить зависимости:
  - fastapi;
  - uvicorn;
  - pydantic;
  - pydantic-settings;
  - sqlalchemy;
  - alembic;
  - asyncpg или psycopg;
  - python-jose или pyjwt;
  - passlib, если нужен;
  - python-multipart, если нужен;
- добавить `.env.example`.

### 2. Настройки

В `core/config.py` описать настройки:

```txt
APP_NAME
ENV
DATABASE_URL
JWT_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
FRONTEND_ORIGIN
```

### 3. Database

В `core/database.py`:
- создать SQLAlchemy engine/session;
- использовать SQLAlchemy 2 style;
- желательно async SQLAlchemy, но sync допустим, если проще и стабильно;
- сделать dependency для session в `api/deps.py`.

### 4. Enums

В `core/enums.py`:
- UserRole;
- ProjectStatus;
- ProjectType;
- ProjectPriority;
- ProjectResponseStatus;
- ProjectMemberRole.

### 5. Модели

Создать SQLAlchemy-модели:
- User;
- Project;
- ProjectMember;
- ProjectResponse;
- ProjectTag;
- ProjectTagLink.

Добавить nullable даты для проектов.

Желательно использовать UUID primary key.

### 6. Alembic

- настроить alembic;
- создать миграцию для всех таблиц;
- проверить, что миграция применима к PostgreSQL.

### 7. Users/Auth

Реализовать упрощённую авторизацию:

Endpoints:
- `POST /api/auth/request-code`
- `POST /api/auth/verify-code`
- `GET /api/me`

MVP-логика:
- принимать email;
- проверять домен `@utmn.ru`;
- для dev-режима можно считать код всегда `000000`;
- если пользователя нет, создать пользователя с ролью `employee`;
- если email `admin@utmn.ru`, дать роль `admin`;
- если email `manager@utmn.ru`, дать роль `project_manager`;
- вернуть JWT.

### 8. Projects public API

Endpoints:
- `GET /api/projects`;
- `GET /api/projects/{project_id}`;
- `POST /api/projects/{project_id}/responses`.

Функциональность:
- список проектов карточками;
- фильтр по статусу;
- фильтр по типу;
- поиск по названию;
- сортировка по дате создания / приоритету;
- не показывать archived/draft в публичной витрине;
- в списке возвращать `responses_count`.

### 9. Admin projects API

Endpoints:
- `GET /api/admin/projects`;
- `POST /api/admin/projects`;
- `PATCH /api/admin/projects/{project_id}`;
- `DELETE /api/admin/projects/{project_id}`;
- `GET /api/admin/projects/{project_id}/responses`.

Функциональность:
- создать проект;
- редактировать проект;
- архивировать проект;
- смотреть все проекты, включая draft/archived;
- смотреть отклики проекта.

### 10. Admin responses API

Endpoints:
- `GET /api/admin/responses`;
- `PATCH /api/admin/responses/{response_id}`.

Функциональность:
- список всех откликов;
- фильтр по проекту;
- фильтр по статусу;
- поиск по ФИО/email;
- изменение статуса отклика.

### 11. Stats API

Endpoint:
- `GET /api/admin/stats`.

Метрики:
- всего проектов;
- активных проектов;
- архивных проектов;
- всего откликов;
- новых откликов;
- принятых откликов;
- отклонённых откликов;
- отклики по проектам.

### 12. Seed

Создать `scripts/seed.py`.

Seed должен создавать:
- admin@utmn.ru;
- manager@utmn.ru;
- employee@utmn.ru;
- несколько проектов;
- несколько откликов.

### 13. README

В backend README описать:

```bash
cp .env.example .env
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## Acceptance criteria backend

Backend считается готовым, если:

- приложение стартует;
- миграции применяются;
- seed создаёт демо-данные;
- Swagger доступен;
- можно получить список проектов;
- можно открыть проект;
- можно отправить отклик;
- можно авторизоваться через `@utmn.ru`;
- admin может создать проект;
- admin может архивировать проект;
- admin может посмотреть отклики;
- admin может изменить статус отклика;
- stats endpoint возвращает данные.
