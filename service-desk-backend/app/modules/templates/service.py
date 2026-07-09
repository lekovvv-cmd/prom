import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.core.enums import TemplateVersionStatus
from app.modules.catalog.repository import CatalogRepository
from app.modules.templates import schemas
from app.modules.templates.models import ServiceDeskTemplateVersion
from app.modules.templates.repository import TemplateRepository


class TemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TemplateRepository(db)
        self.catalog_repository = CatalogRepository(db)

    def list_versions(self, service_id: uuid.UUID) -> list[ServiceDeskTemplateVersion]:
        self._require_service(service_id)
        return self.repository.list_versions(service_id)

    def create_version(
        self,
        service_id: uuid.UUID,
        payload: schemas.TemplateVersionCreate,
    ) -> ServiceDeskTemplateVersion:
        self._require_service(service_id)
        version = ServiceDeskTemplateVersion(
            service_id=service_id,
            version=self.repository.next_version_number(service_id),
            status=TemplateVersionStatus.DRAFT,
            system_settings=payload.system_settings,
        )
        self.repository.add_version(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion:
        return self._require_version(version_id)

    def update_version(
        self,
        version_id: uuid.UUID,
        payload: schemas.TemplateVersionUpdate,
    ) -> ServiceDeskTemplateVersion:
        version = self._require_version(version_id)
        self._ensure_draft(version)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(version, field, value)
        self.db.commit()
        self.db.refresh(version)
        return version

    def publish_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion:
        version = self._require_version(version_id)
        self._ensure_draft(version)
        now = utc_now()
        current = self.repository.get_published_version(version.service_id)
        if current:
            current.status = TemplateVersionStatus.ARCHIVED
            current.archived_at = now

        version.status = TemplateVersionStatus.PUBLISHED
        version.published_at = now
        version.archived_at = None
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_published_form(self, service_id: uuid.UUID) -> schemas.PublishedTemplateRead:
        self._require_service(service_id)
        version = self.repository.get_published_version(service_id)
        if not version:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Опубликованный шаблон услуги не найден")
        return schemas.PublishedTemplateRead(service_id=service_id, template_version=version, fields=[])

    def _require_service(self, service_id: uuid.UUID) -> None:
        if not self.catalog_repository.get_service(service_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")

    def _require_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion:
        version = self.repository.get_version(version_id)
        if not version:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Версия шаблона не найдена")
        return version

    def _ensure_draft(self, version: ServiceDeskTemplateVersion) -> None:
        if version.status != TemplateVersionStatus.DRAFT:
            raise HTTPException(status.HTTP_409_CONFLICT, "Редактировать можно только черновик шаблона")
