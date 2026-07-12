import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db
from app.core.enums import ServiceDeskTicketAction, ServiceDeskTicketStatus
from app.modules.approvals import schemas as approval_schemas
from app.modules.approvals.schemas import TicketApprovalStageRead
from app.modules.attachments import schemas as attachment_schemas
from app.modules.attachments.service import AttachmentService
from app.modules.comments import schemas as comment_schemas
from app.modules.comments.service import TicketCommentService
from app.modules.tickets import schemas
from app.modules.tickets.service import TicketService
from app.modules.templates import schemas as template_schemas
from app.modules.templates.service import TemplateService

router = APIRouter(tags=["tickets"])


@router.post("/tickets/drafts", response_model=schemas.TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket_draft(
    payload: schemas.TicketDraftCreate,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).create_draft(payload, current_user)


@router.patch("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def update_ticket_draft(
    ticket_id: uuid.UUID,
    payload: schemas.TicketDraftUpdate,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).update_draft(ticket_id, payload, current_user)


@router.post("/tickets/{ticket_id}/submit", response_model=schemas.TicketRead)
def submit_ticket_draft(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).submit_draft(ticket_id, current_user)


@router.get("/tickets/{ticket_id}/form", response_model=template_schemas.PublishedTemplateRead)
def get_ticket_form(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    ticket = TicketService(db).get_draft_for_edit(ticket_id, current_user)
    return TemplateService(db).get_version_form(ticket.template_version_id)


@router.post("/tickets/{ticket_id}/assign", response_model=schemas.TicketRead)
def assign_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketAssignmentAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).assign_ticket(ticket_id, payload, current_user)


@router.post("/tickets/{ticket_id}/reassign", response_model=schemas.TicketRead)
def reassign_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketAssignmentAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).reassign_ticket(ticket_id, payload, current_user)


@router.post("/tickets/{ticket_id}/start", response_model=schemas.TicketRead)
def start_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.START,
        current_user,
    )


@router.post("/tickets/{ticket_id}/request-clarification", response_model=schemas.TicketRead)
def request_ticket_clarification(
    ticket_id: uuid.UUID,
    payload: schemas.TicketCommentAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.REQUEST_CLARIFICATION,
        current_user,
        metadata={"comment": payload.comment},
    )


@router.post("/tickets/{ticket_id}/wait-external", response_model=schemas.TicketRead)
def wait_for_external_action(
    ticket_id: uuid.UUID,
    payload: schemas.TicketReasonAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.WAIT_EXTERNAL,
        current_user,
        metadata={"reason": payload.reason},
    )


@router.post("/tickets/{ticket_id}/resume", response_model=schemas.TicketRead)
def resume_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.RESUME,
        current_user,
    )


@router.post("/tickets/{ticket_id}/resolve", response_model=schemas.TicketRead)
def resolve_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketResolveAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.RESOLVE,
        current_user,
        metadata={
            "resolution_summary": payload.resolution_summary,
            "comment": payload.comment,
        },
    )


@router.post("/tickets/{ticket_id}/close", response_model=schemas.TicketRead)
def close_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.CLOSE,
        current_user,
    )


@router.post("/tickets/{ticket_id}/cancel", response_model=schemas.TicketRead)
def cancel_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketReasonAction,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.CANCEL,
        current_user,
        metadata={"reason": payload.reason},
    )


@router.get(
    "/tickets/{ticket_id}/comments",
    response_model=list[comment_schemas.TicketCommentRead],
)
def list_ticket_comments(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketCommentService(db).list_comments(ticket_id, current_user)


@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=comment_schemas.TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_comment(
    ticket_id: uuid.UUID,
    payload: comment_schemas.TicketCommentCreate,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketCommentService(db).create_comment(ticket_id, payload, current_user)


@router.patch(
    "/tickets/{ticket_id}/comments/{comment_id}",
    response_model=comment_schemas.TicketCommentRead,
)
def update_ticket_comment(
    ticket_id: uuid.UUID,
    comment_id: uuid.UUID,
    payload: comment_schemas.TicketCommentUpdate,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketCommentService(db).update_comment(ticket_id, comment_id, payload, current_user)


@router.delete("/tickets/{ticket_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_comment(
    ticket_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    TicketCommentService(db).delete_comment(ticket_id, comment_id, current_user)


@router.get(
    "/tickets/{ticket_id}/attachments",
    response_model=list[attachment_schemas.ServiceDeskAttachmentRead],
)
def list_ticket_attachments(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return AttachmentService(db).list_ticket_attachments(ticket_id, current_user)


@router.post(
    "/tickets/{ticket_id}/attachments",
    response_model=attachment_schemas.ServiceDeskAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_ticket_attachment(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    file: UploadFile = File(),
    db: Session = Depends(get_db),
):
    return await AttachmentService(db).upload_ticket_attachment(ticket_id, file, current_user)


@router.get("/tickets/{ticket_id}/attachments/{attachment_id}/download", response_class=FileResponse)
def download_ticket_attachment(
    ticket_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    attachment, path = AttachmentService(db).get_downloadable_attachment(
        ticket_id,
        attachment_id,
        current_user,
    )
    return FileResponse(
        path,
        media_type=attachment.content_type or "application/octet-stream",
        filename=attachment.file_name,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get(
    "/tickets/{ticket_id}/fields/{field_key}/attachments",
    response_model=list[attachment_schemas.ServiceDeskAttachmentRead],
)
def list_field_attachments(
    ticket_id: uuid.UUID,
    field_key: str,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return AttachmentService(db).list_field_attachments(ticket_id, field_key, current_user)


@router.post(
    "/tickets/{ticket_id}/fields/{field_key}/attachments",
    response_model=attachment_schemas.ServiceDeskAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_field_attachment(
    ticket_id: uuid.UUID,
    field_key: str,
    current_user: CurrentServiceDeskUser,
    file: UploadFile = File(),
    db: Session = Depends(get_db),
):
    return await AttachmentService(db).upload_field_attachment(ticket_id, field_key, file, current_user)


@router.get(
    "/tickets/{ticket_id}/comments/{comment_id}/attachments",
    response_model=list[attachment_schemas.ServiceDeskAttachmentRead],
)
def list_comment_attachments(
    ticket_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return AttachmentService(db).list_comment_attachments(ticket_id, comment_id, current_user)


@router.post(
    "/tickets/{ticket_id}/comments/{comment_id}/attachments",
    response_model=attachment_schemas.ServiceDeskAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_comment_attachment(
    ticket_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    file: UploadFile = File(),
    db: Session = Depends(get_db),
):
    return await AttachmentService(db).upload_comment_attachment(ticket_id, comment_id, file, current_user)


@router.get(
    "/tickets/{ticket_id}/approvals",
    response_model=list[TicketApprovalStageRead],
)
def get_ticket_approvals(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).get_approval_snapshot(ticket_id, current_user)


@router.post(
    "/tickets/{ticket_id}/approvals/{approval_id}/approve",
    response_model=schemas.TicketRead,
)
def approve_ticket(
    ticket_id: uuid.UUID,
    approval_id: uuid.UUID,
    payload: approval_schemas.TicketApprovalDecision,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).approve_ticket(ticket_id, approval_id, payload, current_user)


@router.post(
    "/tickets/{ticket_id}/approvals/{approval_id}/reject",
    response_model=schemas.TicketRead,
)
def reject_ticket(
    ticket_id: uuid.UUID,
    approval_id: uuid.UUID,
    payload: approval_schemas.TicketApprovalRejection,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).reject_ticket(ticket_id, approval_id, payload, current_user)


@router.get("/me/tickets", response_model=list[schemas.TicketRead])
def list_my_tickets(
    current_user: CurrentServiceDeskUser,
    status_filter: ServiceDeskTicketStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    return TicketService(db).list_user_tickets(current_user, status_filter=status_filter)


@router.get("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def get_ticket(
    ticket_id: uuid.UUID,
    current_user: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return TicketService(db).get_ticket_for_actor(ticket_id, current_user)
