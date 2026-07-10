import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.core.enums import TemplateVersionStatus
from app.modules.assignments.policy import AssigneePolicy
from app.modules.approvals.service import ApprovalWorkflowService
from app.modules.catalog.repository import CatalogRepository
from app.modules.templates import schemas
from app.modules.templates.models import (
    ServiceDeskDictionary,
    ServiceDeskDictionaryItem,
    ServiceDeskTemplateField,
    ServiceDeskTemplateVersion,
)
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.validation import validate_template_payload


class TemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TemplateRepository(db)
        self.catalog_repository = CatalogRepository(db)
        self.approval_workflow_service = ApprovalWorkflowService(db)

    def list_versions(self, service_id: uuid.UUID) -> list[ServiceDeskTemplateVersion]:
        self._require_service(service_id)
        return self.repository.list_versions(service_id)

    def create_version(
        self,
        service_id: uuid.UUID,
        payload: schemas.TemplateVersionCreate,
    ) -> ServiceDeskTemplateVersion:
        self._require_service(service_id)
        if payload.default_assignee_user_id:
            AssigneePolicy(self.db).require_eligible_assignee(payload.default_assignee_user_id)
        version = ServiceDeskTemplateVersion(
            service_id=service_id,
            version=self.repository.next_version_number(service_id),
            status=TemplateVersionStatus.DRAFT,
            system_settings=payload.system_settings,
            default_assignee_user_id=payload.default_assignee_user_id,
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
        if data.get("default_assignee_user_id"):
            AssigneePolicy(self.db).require_eligible_assignee(data["default_assignee_user_id"])
        for field, value in data.items():
            setattr(version, field, value)
        self.db.commit()
        self.db.refresh(version)
        return version

    def publish_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion:
        version = self._require_version(version_id)
        self._ensure_draft(version)
        self.approval_workflow_service.validate_for_publish(version)
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
        fields = sorted(version.fields, key=lambda field: (field.position, field.label))
        return schemas.PublishedTemplateRead(service_id=service_id, template_version=version, fields=fields)

    def preview_version(self, version_id: uuid.UUID) -> schemas.TemplatePreviewRead:
        version = self._require_version(version_id)
        fields = [
            self._build_field_preview(field)
            for field in sorted(version.fields, key=lambda item: (item.position, item.label))
        ]
        return schemas.TemplatePreviewRead(template_version=version, fields=fields)

    def create_field(
        self,
        version_id: uuid.UUID,
        payload: schemas.TemplateFieldCreate,
    ) -> ServiceDeskTemplateField:
        version = self._require_version(version_id)
        self._ensure_draft(version)
        if self.repository.get_field_by_key(version_id, payload.key):
            raise HTTPException(status.HTTP_409_CONFLICT, "Поле с таким ключом уже есть в шаблоне")
        self._ensure_dictionary_exists(payload.dictionary_code)
        field = ServiceDeskTemplateField(template_version_id=version_id, **payload.model_dump())
        self.repository.add_field(field)
        self.db.commit()
        self.db.refresh(field)
        return field

    def update_field(
        self,
        field_id: uuid.UUID,
        payload: schemas.TemplateFieldUpdate,
    ) -> ServiceDeskTemplateField:
        field = self._require_field(field_id)
        self._ensure_draft(field.template_version)
        data = payload.model_dump(exclude_unset=True)
        if "key" in data:
            duplicate = self.repository.get_field_by_key(field.template_version_id, data["key"])
            if duplicate and duplicate.id != field.id:
                raise HTTPException(status.HTTP_409_CONFLICT, "Поле с таким ключом уже есть в шаблоне")
        if "dictionary_code" in data:
            self._ensure_dictionary_exists(data["dictionary_code"])
        for item, value in data.items():
            setattr(field, item, value)
        self.db.commit()
        self.db.refresh(field)
        return field

    def delete_field(self, field_id: uuid.UUID) -> None:
        field = self._require_field(field_id)
        self._ensure_draft(field.template_version)
        self.db.delete(field)
        self.db.commit()

    def reorder_fields(
        self,
        version_id: uuid.UUID,
        payload: schemas.TemplateFieldsReorder,
    ) -> list[ServiceDeskTemplateField]:
        version = self._require_version(version_id)
        self._ensure_draft(version)
        fields_by_id = {field.id: field for field in version.fields}
        if set(fields_by_id) != set(payload.field_ids):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Передайте все поля шаблона в новом порядке")
        for position, field_id in enumerate(payload.field_ids):
            fields_by_id[field_id].position = position
        self.db.commit()
        return sorted(fields_by_id.values(), key=lambda field: field.position)

    def validate_payload(
        self,
        version_id: uuid.UUID,
        payload: schemas.TemplateValidationRequest,
    ) -> schemas.TemplateValidationResult:
        version = self._require_version(version_id)
        return validate_template_payload(version, payload.data)

    def list_dictionaries(self, active: bool | None = None) -> list[ServiceDeskDictionary]:
        return self.repository.list_dictionaries(active=active)

    def create_dictionary(self, payload: schemas.DictionaryCreate) -> ServiceDeskDictionary:
        if self.repository.get_dictionary_by_code(payload.code):
            raise HTTPException(status.HTTP_409_CONFLICT, "Справочник с таким кодом уже существует")
        dictionary = ServiceDeskDictionary(**payload.model_dump())
        self.repository.add_dictionary(dictionary)
        self.db.commit()
        self.db.refresh(dictionary)
        return dictionary

    def update_dictionary(
        self,
        dictionary_id: uuid.UUID,
        payload: schemas.DictionaryUpdate,
    ) -> ServiceDeskDictionary:
        dictionary = self._require_dictionary(dictionary_id)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data:
            duplicate = self.repository.get_dictionary_by_code(data["code"])
            if duplicate and duplicate.id != dictionary.id:
                raise HTTPException(status.HTTP_409_CONFLICT, "Справочник с таким кодом уже существует")
        for item, value in data.items():
            setattr(dictionary, item, value)
        self.db.commit()
        self.db.refresh(dictionary)
        return dictionary

    def create_dictionary_item(
        self,
        dictionary_id: uuid.UUID,
        payload: schemas.DictionaryItemCreate,
    ) -> ServiceDeskDictionaryItem:
        self._require_dictionary(dictionary_id)
        item = ServiceDeskDictionaryItem(
            dictionary_id=dictionary_id,
            label=payload.label,
            value=payload.value,
            position=payload.position,
            is_active=payload.is_active,
            metadata_json=payload.metadata,
        )
        self.repository.add_dictionary_item(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_dictionary_item(
        self,
        item_id: uuid.UUID,
        payload: schemas.DictionaryItemUpdate,
    ) -> ServiceDeskDictionaryItem:
        item = self._require_dictionary_item(item_id)
        data = payload.model_dump(exclude_unset=True)
        if "metadata" in data:
            item.metadata_json = data.pop("metadata")
        for key, value in data.items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

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

    def _require_field(self, field_id: uuid.UUID) -> ServiceDeskTemplateField:
        field = self.repository.get_field(field_id)
        if not field:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Поле шаблона не найдено")
        return field

    def _require_dictionary(self, dictionary_id: uuid.UUID) -> ServiceDeskDictionary:
        dictionary = self.repository.get_dictionary(dictionary_id)
        if not dictionary:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Справочник не найден")
        return dictionary

    def _require_dictionary_item(self, item_id: uuid.UUID) -> ServiceDeskDictionaryItem:
        item = self.repository.get_dictionary_item(item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Значение справочника не найдено")
        return item

    def _ensure_dictionary_exists(self, dictionary_code: str | None) -> None:
        if dictionary_code and not self.repository.get_dictionary_by_code(dictionary_code):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Справочник поля не найден")

    def _build_field_preview(self, field: ServiceDeskTemplateField) -> schemas.TemplateFieldPreviewRead:
        payload = schemas.TemplateFieldRead.model_validate(field).model_dump()
        payload["effective_options"] = self._resolve_field_options(field)
        return schemas.TemplateFieldPreviewRead(**payload)

    def _resolve_field_options(self, field: ServiceDeskTemplateField) -> list[dict]:
        if field.dictionary_code:
            dictionary = self.repository.get_dictionary_by_code(field.dictionary_code)
            if not dictionary:
                return []
            return [
                {
                    "label": item.label,
                    "value": item.value,
                    "position": item.position,
                    "is_active": item.is_active,
                    "metadata": item.metadata_json,
                }
                for item in sorted(dictionary.items, key=lambda item: (item.position, item.label))
                if item.is_active
            ]
        if not field.options:
            return []
        return [
            {
                "label": option.get("label", option.get("value")),
                "value": option.get("value"),
                "position": option.get("position", index),
                "is_active": option.get("is_active", True),
                "metadata": option.get("metadata", {}),
            }
            for index, option in enumerate(field.options)
            if isinstance(option, dict) and option.get("is_active", True)
        ]
