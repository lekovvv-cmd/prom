# RelaxDev requires this exact filename at the repository root.
# Each project runs one role selected at runtime by PROM_SERVICE.
FROM python:3.14.8-slim@sha256:f85c5697265c178cc6887276c55fe16cf3d14ca35c3df6a5eab3b360534a55d2 AS python-build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
COPY packages/python/platform-sdk packages/python/platform-sdk
COPY apps apps
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/opt/access-venv uv sync --locked --no-dev --package prom-access-service --no-editable
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/opt/projects-venv uv sync --locked --no-dev --package shpiu-project-showcase-backend --no-editable

FROM node:24.13.1-alpine@sha256:4f696fbf39f383c1e486030ba6b289a5d9af541642fc78ab197e584a113b9c03 AS frontend-build
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY contracts/generated contracts/generated
COPY packages/frontend packages/frontend
COPY apps apps
RUN npm ci
ENV VITE_PLATFORM_ENVIRONMENT=pilot \
    VITE_ACCESS_API_BASE_URL=/api/access/v1 \
    VITE_API_BASE_URL=/api/projects/v1 \
    VITE_SERVICE_DESK_API_BASE_URL=/api/service-desk/v1
RUN VITE_PLATFORM_ENVIRONMENT=pilot \
    VITE_ACCESS_API_BASE_URL=/api/access/v1 \
    VITE_API_BASE_URL=/api/projects/v1 \
    VITE_SERVICE_DESK_API_BASE_URL=/api/service-desk/v1 \
    npm run build --workspace=@prom/platform-shell

FROM python:3.14.8-slim@sha256:f85c5697265c178cc6887276c55fe16cf3d14ca35c3df6a5eab3b360534a55d2
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
RUN apt-get update && apt-get install -y --no-install-recommends nginx gettext-base ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && /usr/local/bin/python -m pip uninstall --yes pip \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app
COPY --from=python-build /opt/access-venv /opt/access-venv
COPY --from=python-build /opt/projects-venv /opt/projects-venv
COPY --from=python-build /workspace/apps/access-service /workspace/access
COPY --from=python-build /workspace/apps/projects/backend /workspace/projects
COPY --from=frontend-build /workspace/apps/platform-shell/dist /usr/share/nginx/html
COPY apps/platform-shell/nginx.relaxdev.conf.template /etc/nginx/relaxdev.conf.template
COPY apps/platform-shell/nginx.relaxdev.headers.conf /etc/nginx/relaxdev.headers.conf
COPY apps/platform-shell/start-relaxdev.sh /start-relaxdev.sh
COPY deploy/relaxdev/nginx.conf /etc/nginx/nginx.conf
COPY deploy/relaxdev/runtime.py /workspace/runtime.py
RUN chmod +x /start-relaxdev.sh \
    && mkdir -p /tmp/nginx/client-body /tmp/nginx/proxy \
    && chown -R app:app /workspace /etc/nginx/conf.d /tmp/nginx
WORKDIR /workspace
USER app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --start-period=60s --retries=10 CMD ["python", "/workspace/runtime.py", "--health"]
CMD ["python", "/workspace/runtime.py"]
