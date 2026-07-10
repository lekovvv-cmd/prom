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
