from app.core.enums import SERVICE_DESK_CAPABILITIES, ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser
from app.modules.access.schemas import ServiceDeskCapabilitiesRead, ServiceDeskUserRead


class ServiceDeskAccessService:
    @staticmethod
    def capabilities_for(user: ServiceDeskUser) -> list[str]:
        if user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            return list(SERVICE_DESK_CAPABILITIES)
        return sorted({item.capability for item in user.capabilities})

    def user_read(self, user: ServiceDeskUser) -> ServiceDeskUserRead:
        return ServiceDeskUserRead(
            id=user.id,
            identity_user_id=user.identity_user_id,
            email=user.email,
            display_name=user.display_name,
            department=user.department,
            position=user.position,
            access_type=user.access_type,
            is_active=user.is_active,
            capabilities=self.capabilities_for(user),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def capabilities_read(self, user: ServiceDeskUser) -> ServiceDeskCapabilitiesRead:
        return ServiceDeskCapabilitiesRead(capabilities=self.capabilities_for(user))
