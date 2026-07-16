import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.access.models import ServiceDeskUser
from app.modules.access.service import ServiceDeskAccessService


class AssigneePolicy:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_eligible_assignee(self, user_id: uuid.UUID | None) -> ServiceDeskUser | None:
        if user_id is None:
            return None
        user = self.db.get(ServiceDeskUser, user_id)
        if not user or not user.is_active:
            return None
        capabilities = set(ServiceDeskAccessService.capabilities_for(user))
        return user if "service_desk.be_assignee" in capabilities else None

    def list_eligible_assignees(self) -> list[ServiceDeskUser]:
        statement = (
            select(ServiceDeskUser)
            .options(selectinload(ServiceDeskUser.capabilities))
            .where(ServiceDeskUser.is_active.is_(True))
            .order_by(ServiceDeskUser.display_name.asc(), ServiceDeskUser.email.asc())
        )
        return [
            user
            for user in self.db.scalars(statement).all()
            if "service_desk.be_assignee" in ServiceDeskAccessService.capabilities_for(user)
        ]

    def require_eligible_assignee(self, user_id: uuid.UUID) -> ServiceDeskUser:
        user = self.db.get(ServiceDeskUser, user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Исполнитель не найден")
        if not user.is_active:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Исполнитель неактивен")
        capabilities = set(ServiceDeskAccessService.capabilities_for(user))
        if "service_desk.be_assignee" not in capabilities:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Пользователь не может быть назначен исполнителем Service Desk",
            )
        return user
