from uuid import UUID

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import AdminUser, DbSession
from app.modules.attachments.schemas import AttachmentRead
from app.modules.attachments.service import AttachmentService

router = APIRouter(tags=["attachments"])


@router.post("/admin/projects/{project_id}/attachments", response_model=AttachmentRead, status_code=201)
def upload_project_attachment(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return AttachmentService(db).upload_project_file(project_id, file, uploaded_by=current_user.id)


@router.post("/projects/{project_id}/responses/{response_id}/attachments", response_model=AttachmentRead, status_code=201)
def upload_response_attachment(
    project_id: UUID,
    response_id: UUID,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return AttachmentService(db).upload_response_file(project_id, response_id, file)


@router.get("/attachments/{attachment_id}", response_class=FileResponse)
def download_attachment(attachment_id: UUID, db: DbSession) -> FileResponse:
    return AttachmentService(db).get_download(attachment_id)
