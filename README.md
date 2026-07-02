# Витрина проектов ШПИУ

MVP внутренней витрины стратегических проектов. Сотрудник смотрит проекты и отправляет отклик, администратор создаёт проекты, меняет статусы откликов и видит базовую статистику.

## Стек

- Backend: Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React 19, TypeScript, React Router, Feature-Sliced Design.
- Инфраструктура: Docker Compose для PostgreSQL, GitHub Actions для CI/CD.

## Запуск

```bash
docker compose -p shpiu_project_showcase up -d db
```

Backend:

```bash
cd backend
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Открыть:

- приложение: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`

Демо-вход: `admin@utmn.ru`, `employee@utmn.ru`; dev-код всегда `000000`.

## Проверки

```bash
cd backend
pytest

cd ../frontend
npm test
npm run build
```
