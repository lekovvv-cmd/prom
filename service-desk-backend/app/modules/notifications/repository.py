import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.notifications.models import ServiceDeskNotification, ServiceDeskNotificationOutbox


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

    def list_for_recipient(self, recipient_user_id: uuid.UUID, *, unread_only: bool = False, limit: int = 30):
        statement = select(ServiceDeskNotification).where(
            ServiceDeskNotification.recipient_user_id == recipient_user_id
        )
        if unread_only:
            statement = statement.where(ServiceDeskNotification.is_read.is_(False))
        return list(self.db.scalars(statement.order_by(ServiceDeskNotification.created_at.desc()).limit(limit)).all())

    def unread_count(self, recipient_user_id: uuid.UUID) -> int:
        return self.db.scalar(select(func.count()).select_from(ServiceDeskNotification).where(
            ServiceDeskNotification.recipient_user_id == recipient_user_id,
            ServiceDeskNotification.is_read.is_(False),
        )) or 0

    def get_owned(self, notification_id: uuid.UUID, recipient_user_id: uuid.UUID):
        return self.db.scalar(select(ServiceDeskNotification).where(
            ServiceDeskNotification.id == notification_id,
            ServiceDeskNotification.recipient_user_id == recipient_user_id,
        ).with_for_update())

    def mark_all_read(self, recipient_user_id: uuid.UUID, read_at) -> int:
        result = self.db.execute(update(ServiceDeskNotification).where(
            ServiceDeskNotification.recipient_user_id == recipient_user_id,
            ServiceDeskNotification.is_read.is_(False),
        ).values(is_read=True, read_at=read_at))
        return result.rowcount


class NotificationOutboxRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_add(self, record: ServiceDeskNotificationOutbox):
        for item in self.db.new:
            if isinstance(item, ServiceDeskNotificationOutbox) and (
                item.event_id, item.channel, item.recipient
            ) == (record.event_id, record.channel, record.recipient):
                return item
        existing = self.db.scalar(select(ServiceDeskNotificationOutbox).where(
            ServiceDeskNotificationOutbox.event_id == record.event_id,
            ServiceDeskNotificationOutbox.channel == record.channel,
            ServiceDeskNotificationOutbox.recipient == record.recipient,
        ))
        if existing:
            return existing
        self.db.add(record)
        return record

    def ready_for_processing(self, now, *, limit: int = 50):
        return list(self.db.scalars(
            select(ServiceDeskNotificationOutbox).where(
                ServiceDeskNotificationOutbox.status.in_(("pending", "failed")),
                (ServiceDeskNotificationOutbox.next_retry_at.is_(None))
                | (ServiceDeskNotificationOutbox.next_retry_at <= now),
            ).order_by(ServiceDeskNotificationOutbox.created_at).limit(limit).with_for_update(skip_locked=True)
        ).all())
