# Витрина проектов ШПИУ

MVP для внутренней витрины проектов: админ или руководитель проекта создаёт проекты, сотрудник ищет проект по статусу, компетенциям и тексту, отправляет отклик и прикладывает файлы, админ меняет статус отклика и видит обновлённую статистику.

## Стек

- Backend: Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Feature-Sliced Design.
- Инфраструктура: Docker Compose для PostgreSQL, GitHub Actions для CI/CD.

## Быстрый запуск

Нужны Docker, Node.js/npm и Python 3.14.

Windows:

```powershell
.\dev.cmd
```

Linux:

```bash
chmod +x ./dev.sh
./dev.sh
```

Скрипты сами создают `.env`, ставят зависимости, поднимают PostgreSQL, применяют миграции, запускают seed data, backend и frontend. На Windows backend-venv создаётся в `%LOCALAPPDATA%\shpiu_project_showcase\backend-venv-py314`, чтобы Python не ломался из-за кириллицы в пути проекта.

Если проект уже запускался раньше и backend падает на отсутствующей зависимости, запустите скрипт без `--skip-install` / `-SkipInstall`: он проверит текущий `.venv` и доустановит недостающие пакеты.

После запуска:

- приложение: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`

Демо-вход, код всегда `000000`:

- админ: `admin@utmn.ru`
- руководитель проекта: `manager@utmn.ru`
- сотрудник: `employee@utmn.ru`

Остановить backend/frontend: `Ctrl+C` в терминале со скриптом. Остановить PostgreSQL:

```bash
docker compose -p shpiu_project_showcase down
```

## Опции запуска

Windows:

```powershell
.\dev.cmd -SkipInstall
.\dev.cmd -NoDocker
.\dev.cmd -BackendPort 8001 -FrontendPort 5174
```

Linux:

```bash
./dev.sh --skip-install
./dev.sh --no-docker
./dev.sh --backend-port 8001 --frontend-port 5174
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
