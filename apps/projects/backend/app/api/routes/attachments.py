from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from platform_sdk.storage import IncomingFile

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.modules.attachments.schemas import AttachmentRead
from app.modules.attachments.service import AttachmentService
from app.modules.projects.schemas import OkResponse

router = APIRouter(tags=["attachments"])


@router.post("/admin/projects/{project_id}/attachments", response_model=AttachmentRead, status_code=201)
async def upload_project_attachment(
    project_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return await AttachmentService(db).upload_project_file(
        project_id,
        IncomingFile(file.filename or "attachment", file.content_type, file.read),
        actor=current_user,
    )


@router.post("/projects/{project_id}/responses/{response_id}/attachments", response_model=AttachmentRead, status_code=201)
async def upload_response_attachment(
    project_id: UUID,
    response_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return await AttachmentService(db).upload_response_file(
        project_id,
        response_id,
        IncomingFile(file.filename or "attachment", file.content_type, file.read),
        current_user=current_user,
    )


@router.post("/project-tasks/{task_id}/attachments", response_model=AttachmentRead, status_code=201)
async def upload_task_attachment(
    task_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return await AttachmentService(db).upload_task_file(
        task_id,
        IncomingFile(file.filename or "attachment", file.content_type, file.read),
        current_user=current_user,
    )


@router.post(
    "/admin/projects/{project_id}/stages/{stage_id}/attachments",
    response_model=AttachmentRead,
    status_code=201,
)
async def upload_stage_attachment(
    project_id: UUID,
    stage_id: UUID,
    current_user: AdminUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return await AttachmentService(db).upload_stage_file(
        project_id,
        stage_id,
        IncomingFile(file.filename or "attachment", file.content_type, file.read),
        current_user=current_user,
    )


@router.post(
    "/reports/{report_id}/attachments",
    response_model=AttachmentRead,
    status_code=201,
)
async def upload_report_attachment(
    report_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> AttachmentRead:
    return await AttachmentService(db).upload_report_file(
        report_id,
        IncomingFile(file.filename or "attachment", file.content_type, file.read),
        current_user=current_user,
    )


@router.get("/attachments/{attachment_id}")
def download_attachment(
    attachment_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> StreamingResponse:
    attachment, source = AttachmentService(db).get_download(
        attachment_id,
        current_user=current_user,
    )
    file_name = attachment.safe_name or attachment.file_name
    return StreamingResponse(
        _stream_and_close(source),
        media_type=attachment.content_type_detected
        or attachment.content_type
        or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/attachments/{attachment_id}", response_model=OkResponse)
def delete_attachment(
    attachment_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> OkResponse:
    AttachmentService(db).delete_attachment(
        attachment_id,
        current_user=current_user,
    )
    return OkResponse(ok=True)


def _stream_and_close(source):
    try:
        while chunk := source.read(64 * 1024):
            yield chunk
    finally:
        source.close()
