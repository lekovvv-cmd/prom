from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType
from app.modules.attachments.models import Attachment


class AttachmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: dict) -> Attachment:
        attachment = Attachment(**data)
        self.db.add(attachment)
        self.db.flush()
        return attachment

    def get_by_id(self, attachment_id: UUID) -> Attachment | None:
        return self.db.get(Attachment, attachment_id)

    def list_for_owner(self, owner_type: AttachmentOwnerType, owner_id: UUID) -> list[Attachment]:
        query = (
            select(Attachment)
            .where(Attachment.owner_type == owner_type, Attachment.owner_id == owner_id)
            .order_by(Attachment.created_at.asc())
        )
        return list(self.db.scalars(query))
