import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db
from app.modules.sla import schemas
from app.modules.sla.service import SlaService

router = APIRouter(prefix="/admin/sla", tags=["admin-sla"])


@router.get("/calendars", response_model=list[schemas.BusinessCalendarRead])
def list_business_calendars(
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return SlaService(db).list_calendars(actor)


@router.post("/calendars", response_model=schemas.BusinessCalendarRead, status_code=status.HTTP_201_CREATED)
def create_business_calendar(
    payload: schemas.BusinessCalendarCreate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return SlaService(db).create_calendar(payload, actor)


@router.patch("/calendars/{calendar_id}", response_model=schemas.BusinessCalendarRead)
def update_business_calendar(
    calendar_id: uuid.UUID,
    payload: schemas.BusinessCalendarUpdate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return SlaService(db).update_calendar(calendar_id, payload, actor)
