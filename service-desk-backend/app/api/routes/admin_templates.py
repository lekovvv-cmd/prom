import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_service_desk_capability
from app.modules.templates import schemas
from app.modules.templates.service import TemplateService

router = APIRouter(
    prefix="/admin",
    tags=["admin-templates"],
    dependencies=[Depends(require_service_desk_capability("service_desk.manage_templates"))],
)


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


@router.get("/template-versions/{version_id}/preview", response_model=schemas.TemplatePreviewRead)
def preview_template_version(version_id: uuid.UUID, db: Session = Depends(get_db)):
    return TemplateService(db).preview_version(version_id)


@router.post(
    "/template-versions/{version_id}/fields",
    response_model=schemas.TemplateFieldRead,
    status_code=status.HTTP_201_CREATED,
)
def create_template_field(
    version_id: uuid.UUID,
    payload: schemas.TemplateFieldCreate,
    db: Session = Depends(get_db),
):
    return TemplateService(db).create_field(version_id, payload)


@router.patch("/template-fields/{field_id}", response_model=schemas.TemplateFieldRead)
def update_template_field(
    field_id: uuid.UUID,
    payload: schemas.TemplateFieldUpdate,
    db: Session = Depends(get_db),
):
    return TemplateService(db).update_field(field_id, payload)


@router.delete("/template-fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template_field(field_id: uuid.UUID, db: Session = Depends(get_db)):
    TemplateService(db).delete_field(field_id)


@router.post("/template-versions/{version_id}/reorder-fields", response_model=list[schemas.TemplateFieldRead])
def reorder_template_fields(
    version_id: uuid.UUID,
    payload: schemas.TemplateFieldsReorder,
    db: Session = Depends(get_db),
):
    return TemplateService(db).reorder_fields(version_id, payload)


@router.post("/template-versions/{version_id}/validate", response_model=schemas.TemplateValidationResult)
def validate_template_payload(
    version_id: uuid.UUID,
    payload: schemas.TemplateValidationRequest,
    db: Session = Depends(get_db),
):
    return TemplateService(db).validate_payload(version_id, payload)


@router.get("/dictionaries", response_model=list[schemas.DictionaryRead])
def list_dictionaries(active: bool | None = None, db: Session = Depends(get_db)):
    return TemplateService(db).list_dictionaries(active=active)


@router.post("/dictionaries", response_model=schemas.DictionaryRead, status_code=status.HTTP_201_CREATED)
def create_dictionary(payload: schemas.DictionaryCreate, db: Session = Depends(get_db)):
    return TemplateService(db).create_dictionary(payload)


@router.patch("/dictionaries/{dictionary_id}", response_model=schemas.DictionaryRead)
def update_dictionary(
    dictionary_id: uuid.UUID,
    payload: schemas.DictionaryUpdate,
    db: Session = Depends(get_db),
):
    return TemplateService(db).update_dictionary(dictionary_id, payload)


@router.post(
    "/dictionaries/{dictionary_id}/items",
    response_model=schemas.DictionaryItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dictionary_item(
    dictionary_id: uuid.UUID,
    payload: schemas.DictionaryItemCreate,
    db: Session = Depends(get_db),
):
    return TemplateService(db).create_dictionary_item(dictionary_id, payload)


@router.patch("/dictionary-items/{item_id}", response_model=schemas.DictionaryItemRead)
def update_dictionary_item(
    item_id: uuid.UUID,
    payload: schemas.DictionaryItemUpdate,
    db: Session = Depends(get_db),
):
    return TemplateService(db).update_dictionary_item(item_id, payload)
