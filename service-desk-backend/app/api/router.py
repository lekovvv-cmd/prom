from fastapi import APIRouter

from app.api.routes import admin_catalog, catalog, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(catalog.router)
api_router.include_router(admin_catalog.router)
