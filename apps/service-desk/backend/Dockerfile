FROM python:3.14.2-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY packages/python/platform-sdk /workspace/platform-sdk
COPY apps/service-desk/backend /workspace/backend
RUN python -m pip install --upgrade pip \
    && python -m pip install /workspace/platform-sdk /workspace/backend

FROM base AS test
RUN python -m pip install "/workspace/backend[dev]"
WORKDIR /workspace/backend
CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime
RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /workspace/backend/storage/service-desk \
    && chown -R app:app /workspace/backend

WORKDIR /workspace/backend
USER app
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health/ready', timeout=2)"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
