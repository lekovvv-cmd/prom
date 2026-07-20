from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)
from starlette.middleware.base import BaseHTTPMiddleware

_request_id_context: ContextVar[str | None] = ContextVar("prom_request_id", default=None)


class ServiceMetrics:
    def __init__(self, *, service: str, module: str) -> None:
        self.service = service
        self.module = module
        self.registry = CollectorRegistry()
        common = ["service", "module"]
        self.http_requests = Counter(
            "prom_http_requests_total",
            "HTTP requests handled by a PROM service.",
            [*common, "method", "route", "status_code"],
            registry=self.registry,
        )
        self.http_duration = Histogram(
            "prom_http_request_duration_seconds",
            "PROM HTTP request latency.",
            [*common, "method", "route"],
            registry=self.registry,
        )
        self.http_errors = Counter(
            "prom_http_errors_total",
            "PROM HTTP responses with status code 400 or greater.",
            [*common, "method", "route", "status_code"],
            registry=self.registry,
        )
        self.db_pool = Gauge(
            "prom_db_pool_connections",
            "PROM database pool state.",
            [*common, "state"],
            registry=self.registry,
        )
        self.worker_duration = Histogram(
            "prom_worker_iteration_duration_seconds",
            "PROM worker iteration duration.",
            [*common, "worker"],
            registry=self.registry,
        )
        self.worker_failures = Counter(
            "prom_worker_failures_total",
            "PROM worker iteration failures.",
            [*common, "worker"],
            registry=self.registry,
        )
        self.outbox_pending = Gauge(
            "prom_outbox_pending",
            "PROM outbox records waiting for delivery.",
            common,
            registry=self.registry,
        )
        self.outbox_oldest_age = Gauge(
            "prom_outbox_oldest_pending_age_seconds",
            "Age of the oldest pending PROM outbox record.",
            common,
            registry=self.registry,
        )
        self.sla_warnings = Counter(
            "prom_sla_warnings_total",
            "PROM Service Desk SLA warnings emitted.",
            [*common, "metric"],
            registry=self.registry,
        )
        self.sla_breaches = Counter(
            "prom_sla_breaches_total",
            "PROM Service Desk SLA breaches detected.",
            [*common, "metric"],
            registry=self.registry,
        )
        self.business_operations = Counter(
            "prom_business_operations_total",
            "PROM module business operations.",
            [*common, "operation", "outcome"],
            registry=self.registry,
        )

    @property
    def labels(self) -> tuple[str, str]:
        return self.service, self.module

    def observe_http(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        labels = (*self.labels, method, route)
        self.http_requests.labels(*labels, str(status_code)).inc()
        self.http_duration.labels(*labels).observe(duration_seconds)
        if status_code >= 400:
            self.http_errors.labels(*labels, str(status_code)).inc()

    def record_db_pool(self, snapshot: dict[str, int | str]) -> None:
        for state in ("checked_in", "checked_out", "overflow"):
            value = snapshot.get(state)
            if isinstance(value, int):
                self.db_pool.labels(*self.labels, state).set(value)

    def record_outbox(self, snapshot: dict[str, int | float | None]) -> None:
        pending = snapshot.get("pending")
        oldest = snapshot.get("oldest_pending_age_seconds")
        if isinstance(pending, int):
            self.outbox_pending.labels(*self.labels).set(pending)
        self.outbox_oldest_age.labels(*self.labels).set(
            float(oldest) if isinstance(oldest, (int, float)) else 0
        )

    def observe_worker(
        self,
        *,
        worker: str,
        duration_seconds: float,
        failed: bool = False,
    ) -> None:
        self.worker_duration.labels(*self.labels, worker).observe(duration_seconds)
        if failed:
            self.worker_failures.labels(*self.labels, worker).inc()

    def record_business_operation(self, operation: str, *, outcome: str = "success") -> None:
        self.business_operations.labels(*self.labels, operation, outcome).inc()

    def record_sla_warning(self, metric: str) -> None:
        self.sla_warnings.labels(*self.labels, metric).inc()

    def record_sla_breach(self, metric: str) -> None:
        self.sla_breaches.labels(*self.labels, metric).inc()


@lru_cache(maxsize=None)
def get_service_metrics(*, service: str, module: str) -> ServiceMetrics:
    return ServiceMetrics(service=service, module=module)


def get_request_id() -> str | None:
    return _request_id_context.get()


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str, module: str, environment: str) -> None:
        super().__init__()
        self.context = {"service": service, "module": module, "environment": environment}

    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "message": record.getMessage(), **self.context}
        for key in ("request_id", "trace_id", "user_id", "event", "duration_ms", "status_code"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_json_logging(*, service: str, module: str, environment: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service, module, environment))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, metrics: ServiceMetrics | None = None):  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        request_id_token = _request_id_context.set(request_id)
        started = time.perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception:
                duration_seconds = time.perf_counter() - started
                self._observe(request, 500, duration_seconds)
                raise
            response.headers["X-Request-ID"] = request_id
            duration_seconds = time.perf_counter() - started
            self._observe(request, response.status_code, duration_seconds)
            logging.getLogger("prom.http").info(
                "request_completed",
                extra={"event": "request_completed", "request_id": request_id, "status_code": response.status_code, "duration_ms": round(duration_seconds * 1000, 2)},
            )
            return response
        finally:
            _request_id_context.reset(request_id_token)

    def _observe(self, request: Request, status_code: int, duration_seconds: float) -> None:
        if self.metrics is None:
            return
        route = getattr(request.scope.get("route"), "path", "unmatched")
        self.metrics.observe_http(
            method=request.method,
            route=str(route),
            status_code=status_code,
            duration_seconds=duration_seconds,
        )


def install_request_context(
    app: FastAPI,
    *,
    metrics: ServiceMetrics | None = None,
) -> None:
    app.add_middleware(RequestContextMiddleware, metrics=metrics)


def install_metrics_endpoint(app: FastAPI, metrics: ServiceMetrics) -> None:
    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(
            content=generate_latest(metrics.registry),
            media_type=CONTENT_TYPE_LATEST,
        )


def start_worker_metrics_server(metrics: ServiceMetrics, *, port: int = 9100) -> None:
    start_http_server(port, registry=metrics.registry)
