# Витрина проектов ШПИУ

MVP внутренней витрины проектов: администратор создает проекты и обрабатывает отклики, сотрудник смотрит витрину и отправляет заявку на участие. Статистика обновляется по проектам и откликам.

## Стек

- Backend: Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React 19, TypeScript, React Router, Feature-Sliced Design.
- Инфраструктура: Docker Compose для PostgreSQL, GitHub Actions для CI/CD.

## Быстрый запуск

Нужны Docker, Node.js и Python 3.14.

Windows:

```powershell
.\dev.cmd
```

Linux:

```bash
chmod +x ./dev.sh
./dev.sh
```

Скрипт сам:

- поднимет PostgreSQL через Docker Compose;
- создаст `backend/.env` и `frontend/.env`, если их нет;
- создаст backend virtualenv;
- установит backend/frontend зависимости при первом запуске;
- применит Alembic-миграции;
- заполнит демо-данные;
- запустит backend и frontend.

После запуска открой:

- приложение: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`

Демо-вход:

- админ: `admin@utmn.ru`
- сотрудник: `employee@utmn.ru`
- dev-код: `000000`

Чтобы остановить backend и frontend, нажми `Ctrl+C` в терминале со скриптом. PostgreSQL останется запущенным в Docker; остановить его можно командой:

```bash
docker compose -p shpiu_project_showcase down
```

## Полезные опции

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
