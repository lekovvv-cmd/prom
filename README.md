# Витрина проектов ШПИУ

MVP для внутренней витрины проектов: админ или руководитель проекта создаёт проекты, сотрудник ищет проект по статусу, компетенциям и тексту, отправляет отклик и прикладывает файлы, админ меняет статус отклика и видит обновлённую статистику.

PROM также включает Service Desk: публичный каталог услуг (`/service-desk`), динамические формы с черновиками и вложениями, «Мои заявки», карточку заявки с SLA/историей/действиями и capability-guarded настройки каталога, шаблонов, справочников, согласований, маршрутизации, SLA и доступа. Переключение между модулями доступно в общем Header.

## Стек

- Backend: Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Feature-Sliced Design.
- Инфраструктура: Docker Compose для PostgreSQL, GitHub Actions для CI/CD.

## Быстрый запуск

Для обычного запуска нужны только Docker Desktop и Docker Compose. Python и Node.js на хосте не требуются.

Windows:

```powershell
.\dev.cmd
```

Linux:

```bash
chmod +x ./dev.sh
./dev.sh
```

Скрипты являются тонкими обёртками над Docker Compose. Compose поднимает обе базы, применяет миграции, выполняет идемпотентные seed и identity bootstrap, затем запускает оба API, SLA worker и frontend.

После запуска:

- selector PROM: `http://localhost:5173/`
- Projects: `http://localhost:5173/projects`
- Service Desk: `http://localhost:5173/service-desk`
- Projects Swagger: `http://localhost:8000/docs`
- Service Desk Swagger: `http://localhost:8001/docs`

Демо-вход, код всегда `000000`:

- админ: `admin@utmn.ru`
- руководитель проекта: `manager@utmn.ru`
- сотрудник: `employee@utmn.ru`
- аналитик: `analyst@utmn.ru`

Остановить всю платформу:

```bash
./dev.sh down
```

## Управление локальным окружением

Windows:

```powershell
.\dev.cmd up
.\dev.cmd logs service-desk-backend
.\dev.cmd restart service-desk-sla-worker
.\dev.cmd status
.\dev.cmd down
.\dev.cmd reset
.\dev.cmd test
```

Linux:

```bash
./dev.sh up
./dev.sh logs service-desk-backend
./dev.sh restart service-desk-sla-worker
./dev.sh status
./dev.sh down
./dev.sh reset
./dev.sh test
```

## Проверки

Backend:

```bash
cd backend
python -m pytest
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

E2E:

```bash
# backend должен быть доступен на http://localhost:8000,
# frontend должен быть доступен на http://localhost:5173
cd frontend
npm run test:e2e
```

## Service Desk SLA worker

SLA breach and escalation processing runs as a separate long-lived process next
to the Service Desk API. After migrations are applied, start it with:

```bash
cd service-desk-backend
python scripts/sla_worker.py
```

Set `SERVICE_DESK_SLA_WORKER_POLL_INTERVAL_SECONDS` (default: `60`) in the
Service Desk environment to control polling. The process creates a fresh DB
session for each iteration, rolls back a failed iteration, and exits cleanly on
`SIGINT` or `SIGTERM`.

Notification outbox processing is intentionally a bounded one-shot command:

```bash
cd service-desk-backend
python scripts/process_notification_outbox.py
```

Run it from the deployment platform scheduler. It processes at most
`SERVICE_DESK_NOTIFICATION_OUTBOX_BATCH_SIZE` records per invocation; email
records remain `blocked_external` until a real CIT integration is provided.

В CI запускаются три проверки: backend `pytest`, frontend `vitest` + `build`, browser e2e на основном MVP-сценарии.
