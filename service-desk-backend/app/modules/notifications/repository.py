import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.models import ServiceDeskNotification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def exists(self, event_id: uuid.UUID, recipient_user_id: uuid.UUID) -> bool:
        if any(
            isinstance(item, ServiceDeskNotification)
            and item.event_id == event_id
            and item.recipient_user_id == recipient_user_id
            for item in self.db.new
        ):
            return True
        return self.db.scalar(
            select(ServiceDeskNotification.id).where(
                ServiceDeskNotification.event_id == event_id,
                ServiceDeskNotification.recipient_user_id == recipient_user_id,
            )
        ) is not None

    def add(self, notification: ServiceDeskNotification) -> None:
        self.db.add(notification)
