import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskAttachmentOwnerType, ServiceDeskAttachmentStatus
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
        return self.db.scalar(
            select(ServiceDeskAttachment).where(
                ServiceDeskAttachment.id == attachment_id,
                ServiceDeskAttachment.status != ServiceDeskAttachmentStatus.DELETED,
            )
        )

    def get_for_update(self, attachment_id: uuid.UUID) -> ServiceDeskAttachment | None:
        return self.db.scalar(
            select(ServiceDeskAttachment)
            .where(
                ServiceDeskAttachment.id == attachment_id,
                ServiceDeskAttachment.status != ServiceDeskAttachmentStatus.DELETED,
            )
            .with_for_update()
        )

    def list_for_owner(
        self,
        owner_type: ServiceDeskAttachmentOwnerType,
        owner_id: uuid.UUID,
    ) -> list[ServiceDeskAttachment]:
        statement = (
            select(ServiceDeskAttachment)
            .where(
                ServiceDeskAttachment.owner_type == owner_type,
                ServiceDeskAttachment.owner_id == owner_id,
                ServiceDeskAttachment.status == ServiceDeskAttachmentStatus.AVAILABLE,
            )
            .order_by(ServiceDeskAttachment.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def count_for_owner(self, owner_type: ServiceDeskAttachmentOwnerType, owner_id: uuid.UUID) -> int:
        statement = select(func.count()).select_from(ServiceDeskAttachment).where(
            ServiceDeskAttachment.owner_type == owner_type,
            ServiceDeskAttachment.owner_id == owner_id,
            ServiceDeskAttachment.status.in_(
                (
                    ServiceDeskAttachmentStatus.PENDING,
                    ServiceDeskAttachmentStatus.QUARANTINED,
                    ServiceDeskAttachmentStatus.AVAILABLE,
                )
            ),
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
            ServiceDeskAttachment.status == ServiceDeskAttachmentStatus.AVAILABLE,
        )
        if field_key is not None:
            statement = statement.where(ServiceDeskAttachment.field_key == field_key)
        return list(self.db.scalars(statement.order_by(ServiceDeskAttachment.created_at.asc())).all())

    def count_for_field_value(self, ticket_id: uuid.UUID, field_key: str) -> int:
        statement = select(func.count()).select_from(ServiceDeskAttachment).where(
            ServiceDeskAttachment.owner_type == ServiceDeskAttachmentOwnerType.FIELD_VALUE,
            ServiceDeskAttachment.ticket_id == ticket_id,
            ServiceDeskAttachment.field_key == field_key,
            ServiceDeskAttachment.status.in_(
                (
                    ServiceDeskAttachmentStatus.PENDING,
                    ServiceDeskAttachmentStatus.QUARANTINED,
                    ServiceDeskAttachmentStatus.AVAILABLE,
                )
            ),
        )
        return int(self.db.scalar(statement) or 0)

    def list_storage_keys(self) -> set[str]:
        return set(
            self.db.scalars(
                select(ServiceDeskAttachment.storage_key).where(
                    ServiceDeskAttachment.storage_key.is_not(None)
                )
            ).all()
        )

    def list_deleted(self, *, limit: int = 100) -> list[ServiceDeskAttachment]:
        return list(
            self.db.scalars(
                select(ServiceDeskAttachment)
                .where(
                    ServiceDeskAttachment.status == ServiceDeskAttachmentStatus.DELETED
                )
                .order_by(ServiceDeskAttachment.deleted_at.asc())
                .limit(limit)
                .with_for_update(skip_locked=True)
            ).all()
        )

    def list_rejected_before(
        self,
        before: datetime,
        *,
        limit: int = 100,
    ) -> list[ServiceDeskAttachment]:
        return list(
            self.db.scalars(
                select(ServiceDeskAttachment)
                .where(
                    ServiceDeskAttachment.status
                    == ServiceDeskAttachmentStatus.REJECTED,
                    ServiceDeskAttachment.created_at < before,
                )
                .order_by(ServiceDeskAttachment.created_at.asc())
                .limit(limit)
                .with_for_update(skip_locked=True)
            ).all()
        )

    def status_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            select(ServiceDeskAttachment.status, func.count())
            .group_by(ServiceDeskAttachment.status)
        ).all()
        return {
            status.value if hasattr(status, "value") else str(status): int(count)
            for status, count in rows
        }
