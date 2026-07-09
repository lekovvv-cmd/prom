import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import TemplateVersionStatus
from app.modules.templates.models import ServiceDeskTemplateVersion


class TemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_versions(self, service_id: uuid.UUID) -> list[ServiceDeskTemplateVersion]:
        stmt = (
            select(ServiceDeskTemplateVersion)
            .where(ServiceDeskTemplateVersion.service_id == service_id)
            .order_by(ServiceDeskTemplateVersion.version.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion | None:
        return self.db.get(ServiceDeskTemplateVersion, version_id)

    def get_published_version(self, service_id: uuid.UUID) -> ServiceDeskTemplateVersion | None:
        stmt = select(ServiceDeskTemplateVersion).where(
            ServiceDeskTemplateVersion.service_id == service_id,
            ServiceDeskTemplateVersion.status == TemplateVersionStatus.PUBLISHED,
        )
        return self.db.scalar(stmt)

    def next_version_number(self, service_id: uuid.UUID) -> int:
        stmt = select(func.max(ServiceDeskTemplateVersion.version)).where(
            ServiceDeskTemplateVersion.service_id == service_id
        )
        value = self.db.scalar(stmt)
        return int(value or 0) + 1

    def add_version(self, version: ServiceDeskTemplateVersion) -> ServiceDeskTemplateVersion:
        self.db.add(version)
        self.db.flush()
        self.db.refresh(version)
        return version
