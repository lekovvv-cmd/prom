import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import TemplateVersionStatus
from app.modules.templates.models import (
    ServiceDeskDictionary,
    ServiceDeskDictionaryItem,
    ServiceDeskTemplateField,
    ServiceDeskTemplateVersion,
)


class TemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_versions(self, service_id: uuid.UUID) -> list[ServiceDeskTemplateVersion]:
        stmt = (
            select(ServiceDeskTemplateVersion)
            .options(
                joinedload(ServiceDeskTemplateVersion.fields),
                joinedload(ServiceDeskTemplateVersion.service),
            )
            .where(ServiceDeskTemplateVersion.service_id == service_id)
            .order_by(ServiceDeskTemplateVersion.version.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion | None:
        stmt = (
            select(ServiceDeskTemplateVersion)
            .options(
                joinedload(ServiceDeskTemplateVersion.fields),
                joinedload(ServiceDeskTemplateVersion.service),
            )
            .where(ServiceDeskTemplateVersion.id == version_id)
        )
        return self.db.scalar(stmt)

    def get_published_version(self, service_id: uuid.UUID) -> ServiceDeskTemplateVersion | None:
        stmt = select(ServiceDeskTemplateVersion).where(
            ServiceDeskTemplateVersion.service_id == service_id,
            ServiceDeskTemplateVersion.status == TemplateVersionStatus.PUBLISHED,
        ).options(
            joinedload(ServiceDeskTemplateVersion.fields),
            joinedload(ServiceDeskTemplateVersion.service),
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

    def get_field(self, field_id: uuid.UUID) -> ServiceDeskTemplateField | None:
        return self.db.get(ServiceDeskTemplateField, field_id)

    def get_field_by_key(
        self,
        template_version_id: uuid.UUID,
        key: str,
    ) -> ServiceDeskTemplateField | None:
        stmt = select(ServiceDeskTemplateField).where(
            ServiceDeskTemplateField.template_version_id == template_version_id,
            ServiceDeskTemplateField.key == key,
        )
        return self.db.scalar(stmt)

    def add_field(self, field: ServiceDeskTemplateField) -> ServiceDeskTemplateField:
        self.db.add(field)
        self.db.flush()
        self.db.refresh(field)
        return field

    def list_dictionaries(self, *, active: bool | None = None) -> list[ServiceDeskDictionary]:
        stmt = select(ServiceDeskDictionary).options(joinedload(ServiceDeskDictionary.items))
        if active is not None:
            stmt = stmt.where(ServiceDeskDictionary.is_active.is_(active))
        stmt = stmt.order_by(ServiceDeskDictionary.title.asc())
        return list(self.db.scalars(stmt).unique().all())

    def get_dictionary(self, dictionary_id: uuid.UUID) -> ServiceDeskDictionary | None:
        stmt = (
            select(ServiceDeskDictionary)
            .options(joinedload(ServiceDeskDictionary.items))
            .where(ServiceDeskDictionary.id == dictionary_id)
        )
        return self.db.scalar(stmt)

    def get_dictionary_by_code(self, code: str) -> ServiceDeskDictionary | None:
        stmt = (
            select(ServiceDeskDictionary)
            .options(joinedload(ServiceDeskDictionary.items))
            .where(ServiceDeskDictionary.code == code)
        )
        return self.db.scalar(stmt)

    def add_dictionary(self, dictionary: ServiceDeskDictionary) -> ServiceDeskDictionary:
        self.db.add(dictionary)
        self.db.flush()
        self.db.refresh(dictionary)
        return dictionary

    def get_dictionary_item(self, item_id: uuid.UUID) -> ServiceDeskDictionaryItem | None:
        return self.db.get(ServiceDeskDictionaryItem, item_id)

    def add_dictionary_item(self, item: ServiceDeskDictionaryItem) -> ServiceDeskDictionaryItem:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item
