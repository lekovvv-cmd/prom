from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


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
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logging.getLogger("prom.http").info(
            "request_completed",
            extra={"event": "request_completed", "request_id": request_id, "status_code": response.status_code, "duration_ms": round((time.perf_counter() - started) * 1000, 2)},
        )
        return response


def install_request_context(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)

