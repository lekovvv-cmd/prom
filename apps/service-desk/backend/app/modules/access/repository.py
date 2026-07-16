from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.access.models import ServiceDeskUser


class ServiceDeskAccessRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_identity_user_id(self, identity_user_id: str) -> ServiceDeskUser | None:
        return self.db.scalar(
            select(ServiceDeskUser)
            .options(selectinload(ServiceDeskUser.capabilities))
            .where(ServiceDeskUser.identity_user_id == identity_user_id)
        )
