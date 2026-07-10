import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_service_desk_capability
from app.modules.catalog import schemas
from app.modules.catalog.service import CatalogService

router = APIRouter(
    prefix="/admin",
    tags=["admin-catalog"],
    dependencies=[Depends(require_service_desk_capability("service_desk.manage_catalog"))],
)


@router.get("/categories", response_model=list[schemas.CategoryRead])
def admin_list_categories(
    q: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return CatalogService(db).list_categories(q=q, active=active, include_deleted=True)


@router.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
def admin_create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return CatalogService(db).create_category(payload)


@router.patch("/categories/{category_id}", response_model=schemas.CategoryRead)
def admin_update_category(
    category_id: uuid.UUID,
    payload: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
):
    return CatalogService(db).update_category(category_id, payload)


@router.post("/categories/{category_id}/deactivate", response_model=schemas.CategoryRead)
def admin_deactivate_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    return CatalogService(db).deactivate_category(category_id)


@router.post("/categories/{category_id}/restore", response_model=schemas.CategoryRead)
def admin_restore_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    return CatalogService(db).restore_category(category_id)


@router.get("/services", response_model=list[schemas.ServiceRead])
def admin_list_services(
    q: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return CatalogService(db).list_services(
        q=q,
        category_id=category_id,
        active=active,
        include_deleted=True,
    )


@router.post("/services", response_model=schemas.ServiceRead, status_code=status.HTTP_201_CREATED)
def admin_create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db)):
    return CatalogService(db).create_service(payload)


@router.patch("/services/{service_id}", response_model=schemas.ServiceRead)
def admin_update_service(
    service_id: uuid.UUID,
    payload: schemas.ServiceUpdate,
    db: Session = Depends(get_db),
):
    return CatalogService(db).update_service(service_id, payload)


@router.post("/services/{service_id}/deactivate", response_model=schemas.ServiceRead)
def admin_deactivate_service(service_id: uuid.UUID, db: Session = Depends(get_db)):
    return CatalogService(db).deactivate_service(service_id)


@router.post("/services/{service_id}/restore", response_model=schemas.ServiceRead)
def admin_restore_service(service_id: uuid.UUID, db: Session = Depends(get_db)):
    return CatalogService(db).restore_service(service_id)
