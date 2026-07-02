from fastapi import APIRouter

from app.api.routes import admin_projects, admin_responses, admin_stats, auth, projects

api_router = APIRouter()

for router in (
    auth.router,
    projects.router,
    admin_projects.router,
    admin_responses.router,
    admin_stats.router,
):
    api_router.routes.extend(router.routes)
