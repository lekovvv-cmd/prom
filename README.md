# Витрина проектов ШПИУ

PROM объединяет Projects и закрытый Service Desk с общей Projects identity и подписанным JWT.

Service Desk включает защищённый каталог, динамические формы с черновиками и вложениями, «Мои заявки», lifecycle, SLA, уведомления, Workbench и capability-guarded администрирование. В модуль входят только `service_desk_manager`, `service_desk_admin` и `platform_admin`.

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

Прямая команда эквивалентного запуска:

```bash
docker compose up --build -d --wait
```

Скрипты являются тонкими обёртками над Docker Compose. Compose поднимает обе базы, применяет миграции, выполняет идемпотентные seed и identity bootstrap, затем запускает оба API, SLA worker и frontend.

После запуска:

- selector PROM: `http://localhost:5173/`
- Projects: `http://localhost:5173/projects`
- Service Desk: `http://localhost:5173/service-desk`
- Projects Swagger: `http://localhost:8000/docs`
- Service Desk Swagger: `http://localhost:8001/docs`

Демо-вход, код всегда `000000`:

- сотрудник Projects, без Service Desk: `employee@utmn.ru`
- руководитель Projects, без Service Desk: `project.manager@utmn.ru`
- менеджер Service Desk: `sd.manager@utmn.ru`
- администратор Service Desk: `sd.admin@utmn.ru`
- администратор платформы с полным доступом в обоих модулях: `admin@utmn.ru`

Platform roles: `employee`, `project_manager`, `platform_admin`. Независимая Service Desk role
может отсутствовать и имеет значения `service_desk_manager` или `service_desk_admin`.
`platform_admin` проходит все Service Desk guards по подписанному JWT и не требует заранее
созданного локального profile.

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

Production-like E2E:

```bash
docker compose up --build -d --wait
cd frontend
E2E_BASE_URL=http://127.0.0.1:5173 \
E2E_SERVICE_DESK_URL=http://127.0.0.1:5173/service-desk-api \
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

CI сохраняет Projects/Service Desk pytest, ruff, PostgreSQL concurrency и frontend tests/build.
Browser E2E поднимает реальный Docker Compose с PostgreSQL, migrations, bootstrap, SLA worker и
production Nginx. При падении сохраняются Compose ps/logs, Playwright traces и screenshots.

Корпоративный SSO и реальная email delivery остаются внешними интеграциями. Email outbox имеет
статус `blocked_external`. `/metrics`, Prometheus/Grafana и fake SMTP в поставку не входят.
