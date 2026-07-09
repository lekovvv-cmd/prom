import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.modules.templates import schemas
from app.modules.templates.service import TemplateService

router = APIRouter(prefix="/admin", tags=["admin-templates"])


@router.get("/services/{service_id}/versions", response_model=list[schemas.TemplateVersionRead])
def list_template_versions(service_id: uuid.UUID, db: Session = Depends(get_db)):
    return TemplateService(db).list_versions(service_id)


@router.post(
    "/services/{service_id}/versions",
    response_model=schemas.TemplateVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_template_version(
    service_id: uuid.UUID,
    payload: schemas.TemplateVersionCreate | None = None,
    db: Session = Depends(get_db),
):
    return TemplateService(db).create_version(service_id, payload or schemas.TemplateVersionCreate())


@router.get("/template-versions/{version_id}", response_model=schemas.TemplateVersionRead)
def get_template_version(version_id: uuid.UUID, db: Session = Depends(get_db)):
    return TemplateService(db).get_version(version_id)


@router.patch("/template-versions/{version_id}", response_model=schemas.TemplateVersionRead)
def update_template_version(
    version_id: uuid.UUID,
    payload: schemas.TemplateVersionUpdate,
    db: Session = Depends(get_db),
):
    return TemplateService(db).update_version(version_id, payload)


@router.post("/template-versions/{version_id}/publish", response_model=schemas.TemplateVersionRead)
def publish_template_version(version_id: uuid.UUID, db: Session = Depends(get_db)):
    return TemplateService(db).publish_version(version_id)
