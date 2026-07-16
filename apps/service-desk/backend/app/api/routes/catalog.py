import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db
from app.modules.catalog import schemas
from app.modules.catalog.service import CatalogService
from app.modules.templates.schemas import PublishedTemplateRead
from app.modules.templates.service import TemplateService

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[schemas.CategoryRead])
def list_categories(
    _: CurrentServiceDeskUser,
    q: str | None = Query(default=None),
    active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
):
    return CatalogService(db).list_categories(q=q, active=active)


@router.get("/services", response_model=list[schemas.ServiceRead])
def list_services(
    _: CurrentServiceDeskUser,
    q: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
):
    return CatalogService(db).list_services(q=q, category_id=category_id, active=active, public=True)


@router.get("/services/{service_id}", response_model=schemas.ServiceRead)
def get_service(
    service_id: uuid.UUID,
    _: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return CatalogService(db).get_service(service_id, public=True)


@router.get("/services/{service_id}/form", response_model=PublishedTemplateRead)
def get_service_form(
    service_id: uuid.UUID,
    _: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    CatalogService(db).get_service(service_id, public=True)
    return TemplateService(db).get_published_form(service_id)
