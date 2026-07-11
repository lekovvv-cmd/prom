from fastapi import APIRouter

from app.api.routes import (
    access,
    admin_approvals,
    admin_catalog,
    admin_routing,
    admin_sla,
    admin_stats,
    admin_templates,
    catalog,
    health,
    notifications,
    tickets,
    workbench,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(notifications.router)
api_router.include_router(access.router)
api_router.include_router(catalog.router)
api_router.include_router(admin_catalog.router)
api_router.include_router(admin_templates.router)
api_router.include_router(admin_approvals.router)
api_router.include_router(admin_routing.router)
api_router.include_router(admin_sla.router)
api_router.include_router(admin_stats.router)
api_router.include_router(tickets.router)
api_router.include_router(workbench.router)
