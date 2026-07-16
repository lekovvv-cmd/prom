from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db, get_service_desk_access_status
from app.modules.access import schemas
from app.modules.access.service import ServiceDeskAccessService

router = APIRouter(tags=["access"])


@router.get("/access/status")
def get_access_status(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    return {"has_access": get_service_desk_access_status(db, authorization)}


@router.get("/me", response_model=schemas.ServiceDeskUserRead)
def get_me(current_user: CurrentServiceDeskUser):
    return ServiceDeskAccessService().user_read(current_user)


@router.get("/me/capabilities", response_model=schemas.ServiceDeskCapabilitiesRead)
def get_my_capabilities(current_user: CurrentServiceDeskUser):
    return ServiceDeskAccessService().capabilities_read(current_user)


@router.get("/users/options", response_model=list[schemas.ServiceDeskUserOptionRead])
def get_user_options(
    current_user: CurrentServiceDeskUser,
    capability: str | None = Query(default=None, max_length=128),
    db: Session = Depends(get_db),
):
    return ServiceDeskAccessService(db).list_options(capability=capability)
