Stage 1.1: создан отдельный service-desk-backend с FastAPI health и metrics endpoints.
Stage 1.2: добавлена отдельная Service Desk DB-конфигурация, SQLAlchemy Base и Alembic-миграция доступа.
Stage 1.3: добавлен отдельный CI job для Service Desk backend с миграциями, pytest и ruff.
Stage 1.4: добавлен frontend Service Desk API client с отдельным base URL и общим token storage.
