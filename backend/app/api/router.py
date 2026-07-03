from fastapi import APIRouter

from app.api.routes import admin_projects, admin_responses, admin_stats, admin_users, attachments, auth, competencies, projects

api_router = APIRouter()

for router in (
    auth.router,
    competencies.router,
    projects.router,
    attachments.router,
    admin_projects.router,
    admin_responses.router,
    admin_stats.router,
    admin_users.router,
):
    api_router.routes.extend(router.routes)
