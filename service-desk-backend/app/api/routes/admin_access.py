import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db
from app.core.enums import ServiceDeskAccessType
from app.modules.access.schemas import (
    AccessUserCreate,
    AccessUserPage,
    AccessUserUpdate,
    CapabilityReplace,
    ServiceDeskUserRead,
)
from app.modules.access.service import ServiceDeskAccessService

router = APIRouter(prefix="/admin/access/users", tags=["admin-access"])


@router.get("", response_model=AccessUserPage)
def users(
    actor: CurrentServiceDeskUser,
    q: str | None = None,
    access_type: ServiceDeskAccessType | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ServiceDeskAccessService(db).list_users(
        actor, q=q, access_type=access_type, is_active=is_active, page=page, page_size=page_size
    )


@router.post("", response_model=ServiceDeskUserRead, status_code=status.HTTP_201_CREATED)
def create(payload: AccessUserCreate, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return ServiceDeskAccessService(db).create_user(actor, payload)


@router.patch("/{user_id}", response_model=ServiceDeskUserRead)
def update(
    user_id: uuid.UUID,
    payload: AccessUserUpdate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return ServiceDeskAccessService(db).update_user(actor, user_id, payload)


@router.put("/{user_id}/capabilities", response_model=ServiceDeskUserRead)
def capabilities(
    user_id: uuid.UUID,
    payload: CapabilityReplace,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return ServiceDeskAccessService(db).replace_capabilities(actor, user_id, payload.capabilities)


@router.post("/{user_id}/deactivate", response_model=ServiceDeskUserRead)
def deactivate(user_id: uuid.UUID, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return ServiceDeskAccessService(db).set_active(actor, user_id, False)


@router.post("/{user_id}/activate", response_model=ServiceDeskUserRead)
def activate(user_id: uuid.UUID, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return ServiceDeskAccessService(db).set_active(actor, user_id, True)
