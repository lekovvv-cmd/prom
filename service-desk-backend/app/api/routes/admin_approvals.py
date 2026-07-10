import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_service_desk_capability
from app.modules.approvals import schemas
from app.modules.approvals.service import ApprovalWorkflowService

router = APIRouter(
    prefix="/admin",
    tags=["admin-approvals"],
    dependencies=[
        Depends(require_service_desk_capability("service_desk.manage_approval_workflows"))
    ],
)


@router.get(
    "/template-versions/{version_id}/approval-workflow",
    response_model=schemas.ApprovalWorkflowConfigurationRead,
)
def get_approval_workflow(version_id: uuid.UUID, db: Session = Depends(get_db)):
    return ApprovalWorkflowService(db).get_configuration(version_id)


@router.put(
    "/template-versions/{version_id}/approval-workflow",
    response_model=schemas.ApprovalWorkflowConfigurationRead,
)
def configure_approval_workflow(
    version_id: uuid.UUID,
    payload: schemas.ApprovalWorkflowConfigure,
    db: Session = Depends(get_db),
):
    return ApprovalWorkflowService(db).configure(version_id, payload)


@router.post(
    "/approval-workflows/{workflow_id}/stages",
    response_model=schemas.ApprovalWorkflowConfigurationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_approval_stage(
    workflow_id: uuid.UUID,
    payload: schemas.ApprovalStageCreate,
    db: Session = Depends(get_db),
):
    return ApprovalWorkflowService(db).create_stage(workflow_id, payload)


@router.patch(
    "/approval-stages/{stage_id}",
    response_model=schemas.ApprovalWorkflowConfigurationRead,
)
def update_approval_stage(
    stage_id: uuid.UUID,
    payload: schemas.ApprovalStageUpdate,
    db: Session = Depends(get_db),
):
    return ApprovalWorkflowService(db).update_stage(stage_id, payload)


@router.delete("/approval-stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval_stage(stage_id: uuid.UUID, db: Session = Depends(get_db)):
    ApprovalWorkflowService(db).delete_stage(stage_id)


@router.post(
    "/approval-workflows/{workflow_id}/reorder-stages",
    response_model=schemas.ApprovalWorkflowConfigurationRead,
)
def reorder_approval_stages(
    workflow_id: uuid.UUID,
    payload: schemas.ApprovalStagesReorder,
    db: Session = Depends(get_db),
):
    return ApprovalWorkflowService(db).reorder_stages(workflow_id, payload)


@router.post(
    "/approval-stages/{stage_id}/approvers",
    response_model=schemas.ApprovalWorkflowConfigurationRead,
    status_code=status.HTTP_201_CREATED,
)
def add_stage_approver(
    stage_id: uuid.UUID,
    payload: schemas.ApprovalStageApproverCreate,
    db: Session = Depends(get_db),
):
    return ApprovalWorkflowService(db).add_approver(stage_id, payload)


@router.delete(
    "/approval-stage-approvers/{approver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_stage_approver(approver_id: uuid.UUID, db: Session = Depends(get_db)):
    ApprovalWorkflowService(db).delete_approver(approver_id)
