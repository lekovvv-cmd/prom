import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService


class CatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(
        self,
        *,
        q: str | None = None,
        active: bool | None = None,
        include_deleted: bool = False,
    ) -> list[ServiceDeskCategory]:
        stmt = select(ServiceDeskCategory)
        if q:
            stmt = stmt.where(ServiceDeskCategory.title.ilike(f"%{q.strip()}%"))
        if active is not None:
            stmt = stmt.where(ServiceDeskCategory.is_active.is_(active))
        if not include_deleted:
            stmt = stmt.where(ServiceDeskCategory.deleted_at.is_(None))
        stmt = stmt.order_by(ServiceDeskCategory.position.asc(), ServiceDeskCategory.title.asc())
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: uuid.UUID) -> ServiceDeskCategory | None:
        return self.db.get(ServiceDeskCategory, category_id)

    def add_category(self, category: ServiceDeskCategory) -> ServiceDeskCategory:
        self.db.add(category)
        self.db.flush()
        self.db.refresh(category)
        return category

    def list_services(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        active: bool | None = None,
        include_deleted: bool = False,
    ) -> list[ServiceDeskService]:
        stmt: Select[tuple[ServiceDeskService]] = select(ServiceDeskService).options(
            joinedload(ServiceDeskService.category)
        )
        if q:
            value = f"%{q.strip()}%"
            stmt = stmt.where(
                ServiceDeskService.title.ilike(value)
                | ServiceDeskService.short_description.ilike(value)
                | ServiceDeskService.description.ilike(value)
            )
        if category_id:
            stmt = stmt.where(ServiceDeskService.category_id == category_id)
        if active is not None:
            stmt = stmt.where(ServiceDeskService.is_active.is_(active))
        if not include_deleted:
            stmt = stmt.where(ServiceDeskService.deleted_at.is_(None))
        stmt = stmt.order_by(ServiceDeskService.position.asc(), ServiceDeskService.title.asc())
        return list(self.db.scalars(stmt).all())

    def get_service(self, service_id: uuid.UUID) -> ServiceDeskService | None:
        stmt = (
            select(ServiceDeskService)
            .options(joinedload(ServiceDeskService.category))
            .where(ServiceDeskService.id == service_id)
        )
        return self.db.scalar(stmt)

    def add_service(self, service: ServiceDeskService) -> ServiceDeskService:
        self.db.add(service)
        self.db.flush()
        self.db.refresh(service)
        return service
