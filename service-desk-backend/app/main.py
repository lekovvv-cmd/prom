from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    origins = [origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()]
    for default_origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        if default_origin not in origins:
            origins.append(default_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
