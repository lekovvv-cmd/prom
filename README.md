# Витрина проектов ШПИУ

MVP внутренней витрины проектов: администратор создает проекты и обрабатывает отклики, сотрудник смотрит витрину и отправляет заявку на участие. Статистика обновляется по проектам и откликам.

## Стек

- Backend: Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React 19, TypeScript, React Router, Feature-Sliced Design.
- Инфраструктура: Docker Compose для PostgreSQL, GitHub Actions для CI/CD.

## Запуск одной командой

Скрипты запускают PostgreSQL, backend и frontend, создают `.env`, ставят зависимости при первом запуске, применяют миграции и заполняют demo data.

### Windows

Требования: Docker Desktop, Node.js, Python 3.14.

```powershell
.\dev.cmd
```

### Linux

Требования: Docker Engine с `docker compose`, Node.js/npm, Python 3.14, `curl`.

```bash
chmod +x ./dev.sh
./dev.sh
```

Если PostgreSQL уже запущен отдельно, можно не поднимать Docker:

```bash
./dev.sh --no-docker
```

Если проект запускается в одной папке и на Windows, и на Linux: Windows-скрипт использует `backend/.venv`, а Linux-скрипт создаст `backend/.venv-linux`, если увидит Windows-venv без `bin/python`.

Если `backend/.venv` уже существует, но создан старым Python, скрипты автоматически используют `backend/.venv-py314`. Удалять старый venv руками не нужно.

## Адреса

- приложение: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`

Демо-вход:

- админ: `admin@utmn.ru`
- сотрудник: `employee@utmn.ru`
- dev-код: `000000`

Чтобы остановить backend и frontend, нажми `Ctrl+C` в терминале со скриптом. PostgreSQL останется запущенным в Docker; остановить его можно отдельно:

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

Для проверки Linux-скрипта без долгого запуска:

```bash
./dev.sh --help
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
