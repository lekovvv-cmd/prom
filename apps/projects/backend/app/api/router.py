from fastapi import APIRouter

from app.api.routes import (
    admin_projects,
    admin_responses,
    admin_stats,
    admin_users,
    attachments,
    audit,
    auth,
    competencies,
    project_tasks,
    projects,
    reports,
    users,
)

api_router = APIRouter()

for router in (
    auth.router,
    audit.router,
    competencies.router,
    projects.router,
    reports.router,
    users.router,
    attachments.router,
    admin_projects.router,
    admin_responses.router,
    admin_stats.router,
    admin_users.router,
    project_tasks.router,
):
    api_router.routes.extend(router.routes)
