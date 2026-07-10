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


@router.post(
    "/calendars", response_model=schemas.BusinessCalendarRead, status_code=status.HTTP_201_CREATED
)
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


@router.get("/policies", response_model=list[schemas.SlaPolicyRead])
def list_sla_policies(actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return SlaService(db).list_policies(actor)


@router.post("/policies", response_model=schemas.SlaPolicyRead, status_code=status.HTTP_201_CREATED)
def create_sla_policy(
    payload: schemas.SlaPolicyCreate, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)
):
    return SlaService(db).create_policy(payload, actor)


@router.patch("/policies/{policy_id}", response_model=schemas.SlaPolicyRead)
def update_sla_policy(
    policy_id: uuid.UUID,
    payload: schemas.SlaPolicyUpdate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return SlaService(db).update_policy(policy_id, payload, actor)


@router.get("/bindings", response_model=list[schemas.SlaBindingRead])
def list_sla_bindings(actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return SlaService(db).list_bindings(actor)


@router.post(
    "/bindings", response_model=schemas.SlaBindingRead, status_code=status.HTTP_201_CREATED
)
def create_sla_binding(
    payload: schemas.SlaBindingCreate, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)
):
    return SlaService(db).create_binding(payload, actor)


@router.patch("/bindings/{binding_id}", response_model=schemas.SlaBindingRead)
def update_sla_binding(
    binding_id: uuid.UUID,
    payload: schemas.SlaBindingUpdate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return SlaService(db).update_binding(binding_id, payload, actor)
