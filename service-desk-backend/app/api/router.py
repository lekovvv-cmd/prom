from fastapi import APIRouter

from app.api.routes import admin_approvals, admin_catalog, admin_templates, catalog, health, tickets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(catalog.router)
api_router.include_router(admin_catalog.router)
api_router.include_router(admin_templates.router)
api_router.include_router(admin_approvals.router)
api_router.include_router(tickets.router)
