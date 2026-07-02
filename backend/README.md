# Backend

FastAPI backend для MVP «Витрина проектов ШПИУ».

## Запуск

```bash
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -e .
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

API будет доступен на `http://localhost:8000`, Swagger — на `http://localhost:8000/docs`.

## MVP-авторизация

1. `POST /api/auth/request-code` с email на `@utmn.ru`.
2. `POST /api/auth/verify-code` с кодом `000000`.
3. Использовать `access_token` как `Authorization: Bearer <token>`.

Демо-админ: `admin@utmn.ru`.
