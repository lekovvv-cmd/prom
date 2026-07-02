from uuid import UUID

from pydantic import BaseModel


class ResponsesByProject(BaseModel):
    project_id: UUID
    project_title: str
    responses_count: int


class AdminStats(BaseModel):
    projects_total: int
    projects_active: int
    projects_archived: int
    responses_total: int
    responses_new: int
    responses_accepted: int
    responses_rejected: int
    responses_by_project: list[ResponsesByProject]
