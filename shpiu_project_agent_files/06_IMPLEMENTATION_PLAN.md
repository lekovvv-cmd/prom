# 06_IMPLEMENTATION_PLAN.md — порядок реализации

## Общая стратегия

Делай проект итерациями. После каждой итерации приложение должно оставаться запускаемым.

Не пытайся сразу сделать всё идеально. Сначала рабочий вертикальный срез, потом расширение.

## Итерация 1 — каркас проекта

### Backend

- создать backend-папку;
- настроить FastAPI;
- настроить config;
- настроить database;
- настроить alembic;
- сделать health endpoint.

### Frontend

- создать frontend-папку;
- настроить React + TypeScript;
- настроить роутинг;
- создать базовую FSD-структуру;
- сделать простую страницу `/projects`.

Результат:
- backend стартует;
- frontend стартует;
- frontend может обратиться к backend health endpoint.

## Итерация 2 — доменная модель

### Backend

- добавить enums;
- добавить SQLAlchemy-модели;
- добавить миграцию;
- добавить seed.

Результат:
- база создаётся;
- seed наполняет пользователей, проекты и отклики.

## Итерация 3 — публичная витрина проектов

### Backend

- `GET /api/projects`;
- `GET /api/projects/{project_id}`;
- фильтры;
- сортировки;
- responses_count.

### Frontend

- карточка проекта;
- список карточек;
- поиск;
- фильтр;
- сортировка;
- детальная страница.

Результат:
- сотрудник видит проекты и открывает проект.

## Итерация 4 — отклик на проект

### Backend

- `POST /api/projects/{project_id}/responses`;
- валидация email `@utmn.ru`;
- запрет отклика на archived/draft.

### Frontend

- форма отклика;
- success/error state;
- обновление количества откликов.

Результат:
- сотрудник может откликнуться.

## Итерация 5 — авторизация

### Backend

- `POST /api/auth/request-code`;
- `POST /api/auth/verify-code`;
- `GET /api/me`;
- JWT;
- role dependencies.

### Frontend

- login page;
- хранение token;
- auth provider;
- protected admin routes.

Результат:
- пользователь может войти;
- admin routes защищены.

## Итерация 6 — админка проектов

### Backend

- `GET /api/admin/projects`;
- `POST /api/admin/projects`;
- `PATCH /api/admin/projects/{project_id}`;
- `DELETE /api/admin/projects/{project_id}`.

### Frontend

- таблица проектов;
- создание проекта;
- редактирование проекта;
- архивирование проекта.

Результат:
- admin управляет проектами.

## Итерация 7 — админка откликов

### Backend

- `GET /api/admin/responses`;
- `GET /api/admin/projects/{project_id}/responses`;
- `PATCH /api/admin/responses/{response_id}`.

### Frontend

- таблица откликов;
- фильтр по проекту;
- фильтр по статусу;
- изменение статуса.

Результат:
- admin обрабатывает отклики.

## Итерация 8 — статистика

### Backend

- `GET /api/admin/stats`.

### Frontend

- страница `/admin/stats`;
- карточки статистики.

Результат:
- admin видит базовую аналитику.

## Итерация 9 — полировка

- README;
- `.env.example`;
- обработка ошибок;
- empty/loading states;
- базовые тесты, если успеешь;
- проверить полный сценарий.

## Финальный smoke test

Проверить руками:

1. Запустить backend.
2. Применить миграции.
3. Запустить seed.
4. Запустить frontend.
5. Войти как `admin@utmn.ru`.
6. Создать проект.
7. Открыть `/projects`.
8. Открыть созданный проект.
9. Отправить отклик как `employee@utmn.ru`.
10. Вернуться в админку.
11. Найти отклик.
12. Изменить статус на `contacted`.
13. Проверить статистику.
