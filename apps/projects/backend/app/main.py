import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from platform_sdk.database import pool_metrics
from platform_sdk.errors import install_problem_details_handlers
from platform_sdk.observability import (
    configure_json_logging,
    get_service_metrics,
    install_metrics_endpoint,
    install_request_context,
)
from platform_sdk.outbox import outbox_metrics
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine, get_session, pool_config
from app.modules.platform.models import ProjectOutboxEvent

def create_app() -> FastAPI:
    configure_json_logging(service="projects-api", module="projects", environment=settings.env)
    metrics = get_service_metrics(service="projects-api", module="projects")
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

    install_request_context(app, metrics=metrics)
    install_metrics_endpoint(app, metrics)
    install_problem_details_handlers(app)

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

        pool_snapshot = pool_metrics(engine, pool_config)
        outbox_snapshot = outbox_metrics(db, ProjectOutboxEvent)
        metrics.record_db_pool(pool_snapshot)
        metrics.record_outbox(outbox_snapshot)
        return {
            "status": "ready",
            "checks": {"database": "ok", "storage": "ok"},
            "database_pool": pool_snapshot,
            "outbox": outbox_snapshot,
        }

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
