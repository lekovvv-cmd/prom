FROM python:3.14.6-slim@sha256:d3400aa122fa42cf0af0dbe8ec3091b047eac5c8f7e3539f7135e86d855dc015 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/workspace/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY packages/python/platform-sdk packages/python/platform-sdk
COPY apps/access-service/pyproject.toml apps/access-service/pyproject.toml
COPY apps/projects/backend/pyproject.toml apps/projects/backend/pyproject.toml
COPY apps/service-desk/backend apps/service-desk/backend

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --package shpiu-service-desk-backend --no-editable

FROM builder AS test
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --package shpiu-service-desk-backend --extra dev --no-editable
WORKDIR /workspace/apps/service-desk/backend
CMD ["python", "-m", "pytest", "-q"]

FROM python:3.14.6-slim@sha256:d3400aa122fa42cf0af0dbe8ec3091b047eac5c8f7e3539f7135e86d855dc015 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/workspace/.venv/bin:$PATH"

COPY --from=builder /workspace/.venv /workspace/.venv
COPY --from=builder /workspace/apps/service-desk/backend /workspace/backend

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /workspace/backend/storage/service-desk \
    && chown -R app:app /workspace/backend

WORKDIR /workspace/backend
USER app
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health/ready', timeout=2)"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
