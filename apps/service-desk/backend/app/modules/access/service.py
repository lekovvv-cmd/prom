import uuid

from fastapi import HTTPException, status
from sqlalchemy import exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.enums import SERVICE_DESK_CAPABILITIES, ServiceDeskAccessType
from app.modules.access.models import (
    ServiceDeskAccessAuditEvent,
    ServiceDeskUser,
    ServiceDeskUserCapability,
)
from app.modules.access.schemas import (
    AccessUserCreate,
    AccessUserPage,
    AccessUserUpdate,
    ServiceDeskCapabilitiesRead,
    ServiceDeskUserRead,
)


class ServiceDeskAccessService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    @staticmethod
    def capabilities_for(user: ServiceDeskUser) -> list[str]:
        if (
            getattr(user, "_is_platform_admin", False)
            or user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN
        ):
            return list(SERVICE_DESK_CAPABILITIES)
        allowed = set(SERVICE_DESK_CAPABILITIES)
        return sorted({item.capability for item in user.capabilities if item.capability in allowed})

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

    def list_options(self, *, capability: str | None = None):
        assert self.db is not None
        filters = [ServiceDeskUser.is_active.is_(True)]
        if capability:
            if capability not in SERVICE_DESK_CAPABILITIES:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Указаны неизвестные права доступа")
            filters.append(
                or_(
                    ServiceDeskUser.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN,
                    exists().where(
                        ServiceDeskUserCapability.service_desk_user_id == ServiceDeskUser.id,
                        ServiceDeskUserCapability.capability == capability,
                    ),
                )
            )
        users = self.db.scalars(
            select(ServiceDeskUser).where(*filters).order_by(ServiceDeskUser.display_name, ServiceDeskUser.id)
        ).all()
        return [
            {
                "id": user.id,
                "display_name": user.display_name,
                "department": user.department,
                "position": user.position,
            }
            for user in users
        ]

    def require_manage_access(self, actor: ServiceDeskUser) -> None:
        if "service_desk.manage_access" not in self.capabilities_for(actor):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Недостаточно прав для управления доступом Service Desk"
            )

    def list_users(self, actor, *, q, access_type, is_active, page, page_size):
        self.require_manage_access(actor)
        assert self.db is not None
        filters = []
        if q:
            pattern = f"%{q.strip()}%"
            filters.append(
                or_(
                    ServiceDeskUser.display_name.ilike(pattern),
                    ServiceDeskUser.email.ilike(pattern),
                    ServiceDeskUser.department.ilike(pattern),
                    ServiceDeskUser.position.ilike(pattern),
                )
            )
        if access_type:
            filters.append(ServiceDeskUser.access_type == access_type)
        if is_active is not None:
            filters.append(ServiceDeskUser.is_active.is_(is_active))
        total = self.db.scalar(select(func.count(ServiceDeskUser.id)).where(*filters)) or 0
        users = self.db.scalars(
            select(ServiceDeskUser)
            .options(selectinload(ServiceDeskUser.capabilities))
            .where(*filters)
            .order_by(ServiceDeskUser.display_name, ServiceDeskUser.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return AccessUserPage(
            items=[self.user_read(user) for user in users],
            page=page,
            page_size=page_size,
            total=total,
            pages=(total + page_size - 1) // page_size,
        )

    def _validate_capabilities(self, values):
        unique = sorted(set(values))
        unknown = set(unique) - set(SERVICE_DESK_CAPABILITIES)
        if unknown:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Указаны неизвестные права доступа",
            )
        return unique

    def _state(self, user):
        return {
            "email": user.email,
            "display_name": user.display_name,
            "department": user.department,
            "position": user.position,
            "access_type": user.access_type.value,
            "is_active": user.is_active,
            "capabilities": self.capabilities_for(user),
        }

    def _audit(self, actor, target, event_type, before, after):
        assert self.db is not None
        self.db.add(
            ServiceDeskAccessAuditEvent(
                actor_user_id=actor.id,
                target_user_id=target.id,
                event_type=event_type,
                before_state=before,
                after_state=after,
            )
        )

    def _get(self, user_id):
        assert self.db is not None
        user = self.db.scalar(
            select(ServiceDeskUser)
            .options(selectinload(ServiceDeskUser.capabilities))
            .where(ServiceDeskUser.id == user_id)
        )
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь Service Desk не найден")
        return user

    def create_user(self, actor, payload: AccessUserCreate):
        self.require_manage_access(actor)
        assert self.db is not None
        caps = self._validate_capabilities(payload.capabilities)
        user = ServiceDeskUser(**payload.model_dump(exclude={"capabilities"}))
        self.db.add(user)
        try:
            self.db.flush()
            if user.access_type == ServiceDeskAccessType.SERVICE_DESK_MANAGER:
                user.capabilities = [
                    ServiceDeskUserCapability(capability=value, created_by=actor.id)
                    for value in caps
                ]
            self._audit(actor, user, "access_user_created", None, self._state(user))
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Пользователь с таким идентификатором уже существует"
            ) from exc
        return self.user_read(self._get(user.id))

    def update_user(self, actor, user_id: uuid.UUID, payload: AccessUserUpdate):
        self.require_manage_access(actor)
        assert self.db is not None
        user = self._get(user_id)
        before = self._state(user)
        values = payload.model_dump(exclude_unset=True)
        old_type = user.access_type
        if "access_type" in values:
            values["access_type"] = ServiceDeskAccessType(values["access_type"])
            if (
                user.is_active
                and old_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN
                and values["access_type"] != ServiceDeskAccessType.SERVICE_DESK_ADMIN
            ):
                self._require_another_active_admin(user.id)
        for key, value in values.items():
            setattr(
                user,
                key,
                value.strip() if isinstance(value, str) and key != "access_type" else value,
            )
        if (
            old_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN
            and user.access_type == ServiceDeskAccessType.SERVICE_DESK_MANAGER
        ):
            self._replace_rows(user, [], actor)
        event = "access_type_changed" if old_type != user.access_type else "access_profile_updated"
        self.db.flush()
        self._audit(actor, user, event, before, self._state(user))
        self.db.commit()
        return self.user_read(self._get(user.id))

    def _replace_rows(self, user, capabilities, actor):
        user.capabilities.clear()
        self.db.flush()
        user.capabilities.extend(
            ServiceDeskUserCapability(capability=value, created_by=actor.id)
            for value in capabilities
        )

    def replace_capabilities(self, actor, user_id, capabilities):
        self.require_manage_access(actor)
        assert self.db is not None
        user = self._get(user_id)
        if user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Администратор Service Desk всегда имеет все права"
            )
        before = self._state(user)
        self._replace_rows(user, self._validate_capabilities(capabilities), actor)
        self.db.flush()
        self._audit(actor, user, "capabilities_replaced", before, self._state(user))
        self.db.commit()
        return self.user_read(self._get(user.id))

    def set_active(self, actor, user_id, active):
        self.require_manage_access(actor)
        assert self.db is not None
        user = self._get(user_id)
        if (
            not active
            and user.is_active
            and user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN
        ):
            self._require_another_active_admin(user.id)
        before = self._state(user)
        user.is_active = active
        self.db.flush()
        self._audit(
            actor,
            user,
            "access_activated" if active else "access_deactivated",
            before,
            self._state(user),
        )
        self.db.commit()
        return self.user_read(self._get(user.id))

    def _require_another_active_admin(self, excluded_user_id: uuid.UUID) -> None:
        assert self.db is not None
        active_admin_ids = self.db.scalars(
            select(ServiceDeskUser.id)
            .where(
                ServiceDeskUser.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN,
                ServiceDeskUser.is_active.is_(True),
            )
            .with_for_update()
        ).all()
        if not any(user_id != excluded_user_id for user_id in active_admin_ids):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Нельзя отключить последнего активного администратора Service Desk",
            )
