import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.enums import ServiceDeskTicketStatus
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
