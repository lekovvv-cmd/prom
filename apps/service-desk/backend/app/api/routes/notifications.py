import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db
from app.modules.notifications import schemas
from app.modules.notifications.counters import ServiceDeskCounterService
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["service-desk-notifications"])


@router.get("/contextual-counters", response_model=schemas.ServiceDeskCounters)
def contextual_counters(actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return ServiceDeskCounterService(db).for_actor(actor)


@router.get("", response_model=list[schemas.NotificationRead])
def list_notifications(
    actor: CurrentServiceDeskUser,
    unread_only: bool = Query(False),
    limit: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    return NotificationService(db).list_current_user(actor, unread_only=unread_only, limit=limit)


@router.get("/unread-count", response_model=schemas.UnreadCount)
def unread_count(actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return {"count": NotificationService(db).unread_count(actor)}


@router.post("/read-all", response_model=schemas.ReadAllResult)
def read_all(actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return {"marked_read": NotificationService(db).mark_all_read(actor)}


@router.post("/{notification_id}/read", response_model=schemas.NotificationRead)
def read_notification(
    notification_id: uuid.UUID,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return NotificationService(db).mark_read(notification_id, actor)
