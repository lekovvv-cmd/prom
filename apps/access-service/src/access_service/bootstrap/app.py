from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from access_service.api.router import router
from access_service.bootstrap.config import settings
from access_service.infrastructure.database import SessionLocal, engine, pool_config
from access_service.infrastructure.identity import (
    DatabaseSigningKeyStore,
    InternalTokenSigner,
    build_identity_provider,
)
from access_service.infrastructure.sessions import BrowserSessionManager
from platform_sdk.database import pool_metrics
from platform_sdk.errors import install_problem_details_handlers
from platform_sdk.observability import (
    configure_json_logging,
    get_service_metrics,
    install_metrics_endpoint,
    install_request_context,
)


def create_app() -> FastAPI:
    configure_json_logging(service="access-service", module="access", environment=settings.environment)
    metrics = get_service_metrics(service="access-service", module="access")
    app = FastAPI(title="PROM Access Service", version="1.0.0")
    app.state.token_signer = InternalTokenSigner(
        settings,
        DatabaseSigningKeyStore(settings, SessionLocal),
    )
    app.state.identity_provider = build_identity_provider(settings)
    app.state.session_manager = BrowserSessionManager(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_context(app, metrics=metrics)
    install_metrics_endpoint(app, metrics)
    install_problem_details_handlers(app)
    app.include_router(router)

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready")
    def ready() -> dict[str, object]:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        pool_snapshot = pool_metrics(engine, pool_config)
        metrics.record_db_pool(pool_snapshot)
        return {
            "status": "ready",
            "checks": {"database": "ok"},
            "database_pool": pool_snapshot,
        }

    return app


app = create_app()
