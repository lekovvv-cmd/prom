import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.enums import ServiceDeskTicketAction, ServiceDeskTicketStatus
from app.modules.approvals import schemas as approval_schemas
from app.modules.approvals.schemas import TicketApprovalStageRead
from app.modules.tickets import schemas
from app.modules.tickets.service import TicketService

router = APIRouter(tags=["tickets"])


@router.post("/tickets/drafts", response_model=schemas.TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket_draft(payload: schemas.TicketDraftCreate, db: Session = Depends(get_db)):
    return TicketService(db).create_draft(payload)


@router.patch("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def update_ticket_draft(
    ticket_id: uuid.UUID,
    payload: schemas.TicketDraftUpdate,
    db: Session = Depends(get_db),
):
    return TicketService(db).update_draft(ticket_id, payload)


@router.post("/tickets/{ticket_id}/submit", response_model=schemas.TicketRead)
def submit_ticket_draft(ticket_id: uuid.UUID, db: Session = Depends(get_db)):
    return TicketService(db).submit_draft(ticket_id)


@router.post("/tickets/{ticket_id}/start", response_model=schemas.TicketRead)
def start_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketActorAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.START,
        payload.actor_user_id,
    )


@router.post("/tickets/{ticket_id}/request-clarification", response_model=schemas.TicketRead)
def request_ticket_clarification(
    ticket_id: uuid.UUID,
    payload: schemas.TicketCommentAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.REQUEST_CLARIFICATION,
        payload.actor_user_id,
        metadata={"comment": payload.comment},
    )


@router.post("/tickets/{ticket_id}/wait-external", response_model=schemas.TicketRead)
def wait_for_external_action(
    ticket_id: uuid.UUID,
    payload: schemas.TicketReasonAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.WAIT_EXTERNAL,
        payload.actor_user_id,
        metadata={"reason": payload.reason},
    )


@router.post("/tickets/{ticket_id}/resume", response_model=schemas.TicketRead)
def resume_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketActorAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.RESUME,
        payload.actor_user_id,
    )


@router.post("/tickets/{ticket_id}/resolve", response_model=schemas.TicketRead)
def resolve_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketResolveAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.RESOLVE,
        payload.actor_user_id,
        metadata={
            "resolution_summary": payload.resolution_summary,
            "comment": payload.comment,
        },
    )


@router.post("/tickets/{ticket_id}/close", response_model=schemas.TicketRead)
def close_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketActorAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.CLOSE,
        payload.actor_user_id,
    )


@router.post("/tickets/{ticket_id}/cancel", response_model=schemas.TicketRead)
def cancel_ticket(
    ticket_id: uuid.UUID,
    payload: schemas.TicketReasonAction,
    db: Session = Depends(get_db),
):
    return TicketService(db).perform_action(
        ticket_id,
        ServiceDeskTicketAction.CANCEL,
        payload.actor_user_id,
        metadata={"reason": payload.reason},
    )


@router.get(
    "/tickets/{ticket_id}/approvals",
    response_model=list[TicketApprovalStageRead],
)
def get_ticket_approvals(ticket_id: uuid.UUID, db: Session = Depends(get_db)):
    return TicketService(db).get_approval_snapshot(ticket_id)


@router.post(
    "/tickets/{ticket_id}/approvals/{approval_id}/approve",
    response_model=schemas.TicketRead,
)
def approve_ticket(
    ticket_id: uuid.UUID,
    approval_id: uuid.UUID,
    payload: approval_schemas.TicketApprovalDecision,
    db: Session = Depends(get_db),
):
    return TicketService(db).approve_ticket(ticket_id, approval_id, payload)


@router.post(
    "/tickets/{ticket_id}/approvals/{approval_id}/reject",
    response_model=schemas.TicketRead,
)
def reject_ticket(
    ticket_id: uuid.UUID,
    approval_id: uuid.UUID,
    payload: approval_schemas.TicketApprovalRejection,
    db: Session = Depends(get_db),
):
    return TicketService(db).reject_ticket(ticket_id, approval_id, payload)


@router.get("/me/tickets", response_model=list[schemas.TicketRead])
def list_my_tickets(
    requester_user_id: uuid.UUID = Query(),
    status_filter: ServiceDeskTicketStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    return TicketService(db).list_user_tickets(requester_user_id, status_filter=status_filter)


@router.get("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def get_ticket(ticket_id: uuid.UUID, db: Session = Depends(get_db)):
    return TicketService(db).get_ticket(ticket_id)
