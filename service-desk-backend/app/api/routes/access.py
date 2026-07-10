from fastapi import APIRouter

from app.api.deps import CurrentServiceDeskUser
from app.modules.access import schemas
from app.modules.access.service import ServiceDeskAccessService

router = APIRouter(tags=["access"])


@router.get("/me", response_model=schemas.ServiceDeskUserRead)
def get_me(current_user: CurrentServiceDeskUser):
    return ServiceDeskAccessService().user_read(current_user)


@router.get("/me/capabilities", response_model=schemas.ServiceDeskCapabilitiesRead)
def get_my_capabilities(current_user: CurrentServiceDeskUser):
    return ServiceDeskAccessService().capabilities_read(current_user)
