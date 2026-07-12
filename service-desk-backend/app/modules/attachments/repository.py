import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskAttachmentOwnerType
from app.modules.attachments.models import ServiceDeskAttachment


class AttachmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, attachment: ServiceDeskAttachment) -> ServiceDeskAttachment:
        self.db.add(attachment)
        self.db.flush()
        self.db.refresh(attachment)
        return attachment

    def get(self, attachment_id: uuid.UUID) -> ServiceDeskAttachment | None:
        return self.db.get(ServiceDeskAttachment, attachment_id)

    def get_for_update(self, attachment_id: uuid.UUID) -> ServiceDeskAttachment | None:
        return self.db.get(ServiceDeskAttachment, attachment_id, with_for_update=True)

    def delete(self, attachment: ServiceDeskAttachment) -> None:
        self.db.delete(attachment)

    def list_for_owner(
        self,
        owner_type: ServiceDeskAttachmentOwnerType,
        owner_id: uuid.UUID,
    ) -> list[ServiceDeskAttachment]:
        statement = (
            select(ServiceDeskAttachment)
            .where(ServiceDeskAttachment.owner_type == owner_type, ServiceDeskAttachment.owner_id == owner_id)
            .order_by(ServiceDeskAttachment.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def count_for_owner(self, owner_type: ServiceDeskAttachmentOwnerType, owner_id: uuid.UUID) -> int:
        statement = select(func.count()).select_from(ServiceDeskAttachment).where(
            ServiceDeskAttachment.owner_type == owner_type,
            ServiceDeskAttachment.owner_id == owner_id,
        )
        return int(self.db.scalar(statement) or 0)

    def list_for_field_value(
        self,
        ticket_id: uuid.UUID,
        field_key: str | None = None,
    ) -> list[ServiceDeskAttachment]:
        statement = select(ServiceDeskAttachment).where(
            ServiceDeskAttachment.owner_type == ServiceDeskAttachmentOwnerType.FIELD_VALUE,
            ServiceDeskAttachment.ticket_id == ticket_id,
        )
        if field_key is not None:
            statement = statement.where(ServiceDeskAttachment.field_key == field_key)
        return list(self.db.scalars(statement.order_by(ServiceDeskAttachment.created_at.asc())).all())

    def count_for_field_value(self, ticket_id: uuid.UUID, field_key: str) -> int:
        statement = select(func.count()).select_from(ServiceDeskAttachment).where(
            ServiceDeskAttachment.owner_type == ServiceDeskAttachmentOwnerType.FIELD_VALUE,
            ServiceDeskAttachment.ticket_id == ticket_id,
            ServiceDeskAttachment.field_key == field_key,
        )
        return int(self.db.scalar(statement) or 0)
