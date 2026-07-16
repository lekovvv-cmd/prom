FROM python:3.14.2-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY packages/python/platform-sdk /workspace/platform-sdk
COPY apps/access-service/pyproject.toml ./pyproject.toml
COPY apps/access-service/src ./src
COPY apps/access-service/scripts ./scripts
RUN python -m pip install --upgrade pip \
    && python -m pip install /workspace/platform-sdk . \
    && rm -rf /workspace

FROM base AS test
RUN python -m pip install ".[dev]"
CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime
USER app
EXPOSE 8002
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health/ready', timeout=2)"]
CMD ["python", "-m", "uvicorn", "access_service.bootstrap.app:app", "--host", "0.0.0.0", "--port", "8002"]
