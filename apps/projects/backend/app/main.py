import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.core.config import settings
from app.core.database import get_session
from app.core.exceptions import DomainError


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    origins = [origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()]
    if "http://127.0.0.1:5173" not in origins:
        origins.append("http://127.0.0.1:5173")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.get("/api/health", tags=["health"], response_model=None)
    def health(db: Session = Depends(get_session)) -> dict[str, object] | JSONResponse:
        marker: Path | None = None
        try:
            db.execute(text("SELECT 1"))
            uploads_dir = Path(settings.uploads_dir)
            uploads_dir.mkdir(parents=True, exist_ok=True)
            marker = uploads_dir / f".readiness-{uuid.uuid4().hex}"
            marker.write_bytes(b"ok")
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready"},
            )
        finally:
            if marker is not None:
                marker.unlink(missing_ok=True)

        return {"status": "ready", "checks": {"database": "ok", "storage": "ok"}}

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
