Stage 1.1: создан отдельный service-desk-backend с FastAPI health и metrics endpoints.
Stage 1.2: добавлена отдельная Service Desk DB-конфигурация, SQLAlchemy Base и Alembic-миграция доступа.
Stage 1.3: добавлен отдельный CI job для Service Desk backend с миграциями, pytest и ruff.
Stage 1.4: добавлен frontend Service Desk API client с отдельным base URL и общим token storage.
Stage 1.5: добавлена dev-инфраструктура Service Desk DB/env для локального запуска.
Stage 2.1: добавлены Service Desk категории/услуги каталога с public/admin API и миграцией.
Stage 2.2: добавлены версионированные шаблоны услуг с draft/published/archived API.
Stage 2.3: добавлены dynamic поля шаблонов и справочники Service Desk.
Stage 2.4: добавлена backend-валидация dynamic форм с conditional visibility/required rules.
Stage 2.5: добавлен preview шаблона с resolved options из inline values и справочников.
