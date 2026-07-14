import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.modules.assignments.policy import AssigneePolicy
from app.modules.catalog import schemas
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.catalog.repository import CatalogRepository


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CatalogRepository(db)

    def list_categories(
        self,
        *,
        q: str | None = None,
        active: bool | None = None,
        include_deleted: bool = False,
    ) -> list[ServiceDeskCategory]:
        return self.repository.list_categories(q=q, active=active, include_deleted=include_deleted)

    def create_category(self, payload: schemas.CategoryCreate) -> ServiceDeskCategory:
        if payload.parent_id and not self.repository.get_category(payload.parent_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Родительская категория не найдена")
        self._ensure_unique_category_title(payload.title, payload.parent_id)
        category = ServiceDeskCategory(**{**payload.model_dump(), "title": payload.title.strip()})
        try:
            self.repository.add_category(category)
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Категория с таким названием уже существует",
            ) from error
        self.db.refresh(category)
        return category

    def update_category(self, category_id: uuid.UUID, payload: schemas.CategoryUpdate) -> ServiceDeskCategory:
        category = self._require_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "parent_id" in data and data["parent_id"] and not self.repository.get_category(data["parent_id"]):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Родительская категория не найдена")
        next_title = str(data.get("title", category.title)).strip()
        next_parent_id = data.get("parent_id", category.parent_id)
        self._ensure_unique_category_title(
            next_title,
            next_parent_id,
            exclude_id=category.id,
        )
        if "title" in data:
            data["title"] = next_title
        for field, value in data.items():
            setattr(category, field, value)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Категория с таким названием уже существует",
            ) from error
        self.db.refresh(category)
        return category

    def deactivate_category(self, category_id: uuid.UUID) -> ServiceDeskCategory:
        category = self._require_category(category_id)
        category.is_active = False
        category.deleted_at = utc_now()
        self.db.commit()
        self.db.refresh(category)
        return category

    def restore_category(self, category_id: uuid.UUID) -> ServiceDeskCategory:
        category = self._require_category(category_id)
        category.is_active = True
        category.deleted_at = None
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_services(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        active: bool | None = None,
        include_deleted: bool = False,
        public: bool = False,
    ) -> list[ServiceDeskService]:
        services = self.repository.list_services(
            q=q,
            category_id=category_id,
            active=active,
            include_deleted=include_deleted,
        )
        if not public:
            return services
        from app.modules.templates.repository import TemplateRepository

        published_service_ids = TemplateRepository(self.db).list_published_service_ids(
            [service.id for service in services]
        )
        for service in services:
            service._request_form_available = service.id in published_service_ids
        return services

    def get_service(self, service_id: uuid.UUID, *, public: bool = False) -> ServiceDeskService:
        service = self._require_service(service_id)
        if public and (not service.is_active or service.deleted_at is not None):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")
        if public:
            from app.modules.templates.repository import TemplateRepository

            service._request_form_available = TemplateRepository(self.db).get_published_version(service.id) is not None
        return service

    def create_service(self, payload: schemas.ServiceCreate) -> ServiceDeskService:
        self._require_category(payload.category_id)
        self._ensure_unique_service_title(payload.title, payload.category_id)
        if payload.default_assignee_user_id:
            AssigneePolicy(self.db).require_eligible_assignee(payload.default_assignee_user_id)
        service = ServiceDeskService(**{**payload.model_dump(), "title": payload.title.strip()})
        try:
            self.repository.add_service(service)
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Услуга с таким названием уже существует в выбранной категории",
            ) from error
        self.db.refresh(service)
        return service

    def update_service(self, service_id: uuid.UUID, payload: schemas.ServiceUpdate) -> ServiceDeskService:
        service = self._require_service(service_id)
        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data and data["category_id"]:
            self._require_category(data["category_id"])
        next_title = str(data.get("title", service.title)).strip()
        next_category_id = data.get("category_id", service.category_id)
        self._ensure_unique_service_title(
            next_title,
            next_category_id,
            exclude_id=service.id,
        )
        if "title" in data:
            data["title"] = next_title
        if data.get("default_assignee_user_id"):
            AssigneePolicy(self.db).require_eligible_assignee(data["default_assignee_user_id"])
        for field, value in data.items():
            setattr(service, field, value)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Услуга с таким названием уже существует в выбранной категории",
            ) from error
        self.db.refresh(service)
        return service

    def deactivate_service(self, service_id: uuid.UUID) -> ServiceDeskService:
        service = self._require_service(service_id)
        service.is_active = False
        service.deleted_at = utc_now()
        self.db.commit()
        self.db.refresh(service)
        return service

    def restore_service(self, service_id: uuid.UUID) -> ServiceDeskService:
        service = self._require_service(service_id)
        service.is_active = True
        service.deleted_at = None
        self.db.commit()
        self.db.refresh(service)
        return service

    def _require_category(self, category_id: uuid.UUID) -> ServiceDeskCategory:
        category = self.repository.get_category(category_id)
        if not category:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
        return category

    def _require_service(self, service_id: uuid.UUID) -> ServiceDeskService:
        service = self.repository.get_service(service_id)
        if not service:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")
        return service

    def _ensure_unique_category_title(
        self,
        title: str,
        parent_id: uuid.UUID | None,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if self.repository.category_title_exists(title, parent_id, exclude_id=exclude_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Категория с таким названием уже существует",
            )

    def _ensure_unique_service_title(
        self,
        title: str,
        category_id: uuid.UUID,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if self.repository.service_title_exists(title, category_id, exclude_id=exclude_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Услуга с таким названием уже существует в выбранной категории",
            )
