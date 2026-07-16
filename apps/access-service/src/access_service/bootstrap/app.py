from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from access_service.api.router import router
from access_service.bootstrap.config import settings
from access_service.infrastructure.database import SessionLocal
from access_service.infrastructure.identity import InternalTokenSigner
from platform_sdk.errors import install_problem_details_handlers
from platform_sdk.observability import configure_json_logging, install_request_context


def create_app() -> FastAPI:
    configure_json_logging(service="access-service", module="access", environment=settings.environment)
    app = FastAPI(title="PROM Access Service", version="1.0.0")
    app.state.token_signer = InternalTokenSigner(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_context(app)
    install_problem_details_handlers(app)
    app.include_router(router)

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready")
    def ready() -> dict[str, object]:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready", "checks": {"database": "ok"}}

    return app


app = create_app()

