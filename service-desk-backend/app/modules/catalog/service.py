import uuid

from fastapi import HTTPException, status
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
        category = ServiceDeskCategory(**payload.model_dump())
        self.repository.add_category(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category_id: uuid.UUID, payload: schemas.CategoryUpdate) -> ServiceDeskCategory:
        category = self._require_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "parent_id" in data and data["parent_id"] and not self.repository.get_category(data["parent_id"]):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Родительская категория не найдена")
        for field, value in data.items():
            setattr(category, field, value)
        self.db.commit()
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

        templates = TemplateRepository(self.db)
        return [
            service
            for service in services
            if templates.get_published_version(service.id) is not None
        ]

    def get_service(self, service_id: uuid.UUID, *, public: bool = False) -> ServiceDeskService:
        service = self._require_service(service_id)
        if public and (not service.is_active or service.deleted_at is not None):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")
        return service

    def create_service(self, payload: schemas.ServiceCreate) -> ServiceDeskService:
        self._require_category(payload.category_id)
        if payload.default_assignee_user_id:
            AssigneePolicy(self.db).require_eligible_assignee(payload.default_assignee_user_id)
        service = ServiceDeskService(**payload.model_dump())
        self.repository.add_service(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def update_service(self, service_id: uuid.UUID, payload: schemas.ServiceUpdate) -> ServiceDeskService:
        service = self._require_service(service_id)
        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data and data["category_id"]:
            self._require_category(data["category_id"])
        if data.get("default_assignee_user_id"):
            AssigneePolicy(self.db).require_eligible_assignee(data["default_assignee_user_id"])
        for field, value in data.items():
            setattr(service, field, value)
        self.db.commit()
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
