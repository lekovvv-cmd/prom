from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


@dataclass(slots=True)
class PlatformError(Exception):
    code: str
    title: str
    status_code: int
    detail: str
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def type(self) -> str:
        return f"https://prom/errors/{self.code.lower().replace('_', '-')}"


def install_problem_details_handlers(app: FastAPI) -> None:
    @app.exception_handler(PlatformError)
    async def platform_error_handler(request: Request, exc: PlatformError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": exc.type,
                "title": exc.title,
                "status": exc.status_code,
                "detail": exc.detail,
                "code": exc.code,
                "request_id": request_id,
                "errors": exc.errors,
            },
            media_type="application/problem+json",
        )

