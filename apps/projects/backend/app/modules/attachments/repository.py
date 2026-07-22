from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, AttachmentStatus
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
        return self.db.scalar(
            select(Attachment).where(
                Attachment.id == attachment_id,
                Attachment.status != AttachmentStatus.DELETED,
                Attachment.deleted_at.is_(None),
            )
        )

    def get_for_cleanup(self, attachment_id: UUID) -> Attachment | None:
        return self.db.get(Attachment, attachment_id)

    def list_for_owner(self, owner_type: AttachmentOwnerType, owner_id: UUID) -> list[Attachment]:
        query = (
            select(Attachment)
            .where(
                Attachment.owner_type == owner_type,
                Attachment.owner_id == owner_id,
                Attachment.status == AttachmentStatus.AVAILABLE,
                Attachment.deleted_at.is_(None),
            )
            .order_by(Attachment.created_at.asc())
        )
        return list(self.db.scalars(query))

    def count_for_owner(self, owner_type: AttachmentOwnerType, owner_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Attachment)
                .where(
                    Attachment.owner_type == owner_type,
                    Attachment.owner_id == owner_id,
                    Attachment.status != AttachmentStatus.DELETED,
                    Attachment.deleted_at.is_(None),
                )
            )
            or 0
        )

    def list_storage_keys(self) -> set[str]:
        return {
            key
            for key in self.db.scalars(
                select(Attachment.storage_key).where(
                    Attachment.storage_key.is_not(None),
                    Attachment.status != AttachmentStatus.DELETED,
                    Attachment.deleted_at.is_(None),
                )
            )
            if key
        }
