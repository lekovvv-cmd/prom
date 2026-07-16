import uuid
from copy import deepcopy

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.core.enums import ApprovalMode, ServiceDeskAccessType, TemplateVersionStatus
from app.modules.access.models import ServiceDeskUser
from app.modules.approvals import schemas
from app.modules.approvals.models import (
    ServiceDeskApprovalStage,
    ServiceDeskApprovalStageApprover,
    ServiceDeskApprovalWorkflow,
)
from app.modules.approvals.repository import ApprovalWorkflowRepository
from app.modules.templates.models import ServiceDeskTemplateField, ServiceDeskTemplateVersion
from app.modules.templates.repository import TemplateRepository


class ApprovalWorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ApprovalWorkflowRepository(db)
        self.template_repository = TemplateRepository(db)

    def get_configuration(
        self,
        template_version_id: uuid.UUID,
    ) -> schemas.ApprovalWorkflowConfigurationRead:
        version = self._require_version(template_version_id)
        workflow = self.repository.get_workflow_by_version(template_version_id)
        return schemas.ApprovalWorkflowConfigurationRead(
            template_version_id=version.id,
            approval_mode=version.approval_mode,
            workflow=workflow,
        )

    def get_service_configuration(
        self,
        service_id: uuid.UUID,
    ) -> schemas.ServiceApprovalWorkflowConfigurationRead:
        version = self.template_repository.get_published_version(service_id)
        if not version:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Для услуги нет опубликованной версии формы",
            )
        workflow = self.repository.get_workflow_by_version(version.id)
        return schemas.ServiceApprovalWorkflowConfigurationRead(
            template_version=version,
            template_version_id=version.id,
            approval_mode=version.approval_mode,
            workflow=workflow,
        )

    def apply_for_service(
        self,
        service_id: uuid.UUID,
        payload: schemas.ApprovalWorkflowApply,
    ) -> schemas.ServiceApprovalWorkflowConfigurationRead:
        source = self.template_repository.get_published_version(service_id)
        if not source:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Для услуги нет опубликованной версии формы",
            )
        self._validate_apply_payload(payload)

        version = ServiceDeskTemplateVersion(
            service_id=source.service_id,
            version=self.template_repository.next_version_number(source.service_id),
            status=TemplateVersionStatus.DRAFT,
            approval_mode=payload.approval_mode,
            default_assignee_user_id=source.default_assignee_user_id,
            system_settings=deepcopy(source.system_settings),
        )
        self.db.add(version)
        self.db.flush()

        for field in source.fields:
            self.db.add(
                ServiceDeskTemplateField(
                    template_version_id=version.id,
                    key=field.key,
                    label=field.label,
                    field_type=field.field_type,
                    is_required=field.is_required,
                    position=field.position,
                    help_text=field.help_text,
                    placeholder=field.placeholder,
                    options=deepcopy(field.options),
                    dictionary_code=field.dictionary_code,
                    validation=deepcopy(field.validation),
                    visibility_rules=deepcopy(field.visibility_rules),
                    required_rules=deepcopy(field.required_rules),
                )
            )

        if payload.approval_mode == ApprovalMode.WORKFLOW:
            workflow = ServiceDeskApprovalWorkflow(
                template_version_id=version.id,
                name=payload.name,
                is_active=True,
            )
            self.db.add(workflow)
            self.db.flush()
            for position, stage_payload in enumerate(payload.stages):
                stage = ServiceDeskApprovalStage(
                    workflow_id=workflow.id,
                    title=stage_payload.title,
                    decision_rule=stage_payload.decision_rule,
                    position=position,
                )
                self.db.add(stage)
                self.db.flush()
                for approver_id in stage_payload.approver_user_ids:
                    self._require_eligible_approver(approver_id)
                    self.db.add(
                        ServiceDeskApprovalStageApprover(
                            stage_id=stage.id,
                            service_desk_user_id=approver_id,
                        )
                    )

        self.db.flush()
        self.validate_for_publish(version)

        now = utc_now()
        source.status = TemplateVersionStatus.ARCHIVED
        source.archived_at = now
        version.status = TemplateVersionStatus.PUBLISHED
        version.published_at = now
        version.archived_at = None
        self.db.commit()

        return self.get_service_configuration(service_id)

    def configure(
        self,
        template_version_id: uuid.UUID,
        payload: schemas.ApprovalWorkflowConfigure,
    ) -> schemas.ApprovalWorkflowConfigurationRead:
        version = self._require_draft_version(template_version_id)
        workflow = self.repository.get_workflow_by_version(template_version_id)
        version.approval_mode = payload.approval_mode

        if payload.approval_mode == ApprovalMode.WORKFLOW:
            if workflow is None:
                workflow = self.repository.add_workflow(
                    ServiceDeskApprovalWorkflow(
                        template_version_id=template_version_id,
                        name=payload.name,
                        is_active=payload.is_active,
                    )
                )
            else:
                workflow.name = payload.name
                workflow.is_active = payload.is_active
        elif workflow is not None:
            workflow.is_active = False

        self.db.commit()
        return self.get_configuration(version.id)

    def create_stage(
        self,
        workflow_id: uuid.UUID,
        payload: schemas.ApprovalStageCreate,
    ) -> schemas.ApprovalWorkflowConfigurationRead:
        workflow = self._require_workflow(workflow_id)
        version = self._require_draft_version(workflow.template_version_id)
        self._ensure_workflow_mode(version)
        position = payload.position
        if position is None:
            position = max((stage.position for stage in workflow.stages), default=-1) + 1
        self.repository.add_stage(
            ServiceDeskApprovalStage(
                workflow_id=workflow.id,
                title=payload.title,
                decision_rule=payload.decision_rule,
                position=position,
            )
        )
        self.db.commit()
        return self.get_configuration(version.id)

    def update_stage(
        self,
        stage_id: uuid.UUID,
        payload: schemas.ApprovalStageUpdate,
    ) -> schemas.ApprovalWorkflowConfigurationRead:
        stage = self._require_stage(stage_id)
        version = self._require_draft_version(stage.workflow.template_version_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(stage, field, value)
        self.db.commit()
        return self.get_configuration(version.id)

    def delete_stage(self, stage_id: uuid.UUID) -> None:
        stage = self._require_stage(stage_id)
        self._require_draft_version(stage.workflow.template_version_id)
        self.db.delete(stage)
        self.db.commit()

    def reorder_stages(
        self,
        workflow_id: uuid.UUID,
        payload: schemas.ApprovalStagesReorder,
    ) -> schemas.ApprovalWorkflowConfigurationRead:
        workflow = self._require_workflow(workflow_id)
        version = self._require_draft_version(workflow.template_version_id)
        existing_ids = {stage.id for stage in workflow.stages}
        if len(payload.stage_ids) != len(set(payload.stage_ids)) or set(payload.stage_ids) != existing_ids:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Передайте все этапы без повторов")
        by_id = {stage.id: stage for stage in workflow.stages}
        for position, stage_id in enumerate(payload.stage_ids):
            by_id[stage_id].position = position
        self.db.commit()
        return self.get_configuration(version.id)

    def add_approver(
        self,
        stage_id: uuid.UUID,
        payload: schemas.ApprovalStageApproverCreate,
    ) -> schemas.ApprovalWorkflowConfigurationRead:
        stage = self._require_stage(stage_id)
        version = self._require_draft_version(stage.workflow.template_version_id)
        user = self._require_eligible_approver(payload.service_desk_user_id)
        if self.repository.get_stage_approver(stage.id, user.id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь уже добавлен в этап")
        self.repository.add_approver(
            ServiceDeskApprovalStageApprover(
                stage_id=stage.id,
                service_desk_user_id=user.id,
            )
        )
        self.db.commit()
        return self.get_configuration(version.id)

    def delete_approver(self, approver_id: uuid.UUID) -> None:
        approver = self.repository.get_approver(approver_id)
        if not approver:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Согласующий этапа не найден")
        stage = self._require_stage(approver.stage_id)
        self._require_draft_version(stage.workflow.template_version_id)
        self.db.delete(approver)
        self.db.commit()

    def validate_for_publish(self, version: ServiceDeskTemplateVersion) -> None:
        if version.approval_mode == ApprovalMode.NONE:
            return
        workflow = self.repository.get_workflow_by_version(version.id)
        if not workflow or not workflow.is_active:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Настройте активный процесс согласования")
        if not workflow.stages:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Добавьте этап согласования")
        for stage in workflow.stages:
            if not stage.approvers:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Добавьте согласующего в этап «{stage.title}»",
                )
            if any(not approver.user.is_active or not self._can_approve(approver.user) for approver in stage.approvers):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"В этапе «{stage.title}» есть недоступный согласующий",
                )

    def _require_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion:
        version = self.template_repository.get_version(version_id)
        if not version:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Версия шаблона не найдена")
        return version

    def _require_draft_version(self, version_id: uuid.UUID) -> ServiceDeskTemplateVersion:
        version = self._require_version(version_id)
        if version.status != TemplateVersionStatus.DRAFT:
            raise HTTPException(status.HTTP_409_CONFLICT, "Согласование настраивается только для черновой версии")
        return version

    def _require_workflow(self, workflow_id: uuid.UUID) -> ServiceDeskApprovalWorkflow:
        workflow = self.repository.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Процесс согласования не найден")
        return workflow

    def _require_stage(self, stage_id: uuid.UUID) -> ServiceDeskApprovalStage:
        stage = self.repository.get_stage(stage_id)
        if not stage:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Этап согласования не найден")
        return stage

    @staticmethod
    def _validate_apply_payload(payload: schemas.ApprovalWorkflowApply) -> None:
        if payload.approval_mode == ApprovalMode.NONE:
            if payload.stages:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Для отключённого согласования этапы не передаются",
                )
            return
        if not payload.stages:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Добавьте этап согласования")
        for stage in payload.stages:
            if len(stage.approver_user_ids) != len(set(stage.approver_user_ids)):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"В этапе «{stage.title}» есть повторяющиеся согласующие",
                )

    def _require_eligible_approver(self, user_id: uuid.UUID) -> ServiceDeskUser:
        user = self.db.get(ServiceDeskUser, user_id)
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Согласующий неактивен или не найден")
        if not self._can_approve(user):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "У пользователя нет права согласовывать заявки Service Desk",
            )
        return user

    @staticmethod
    def _ensure_workflow_mode(version: ServiceDeskTemplateVersion) -> None:
        if version.approval_mode != ApprovalMode.WORKFLOW:
            raise HTTPException(status.HTTP_409_CONFLICT, "Для версии не включён процесс согласования")

    @staticmethod
    def _can_approve(user: ServiceDeskUser) -> bool:
        return user.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN or any(
            capability.capability == "service_desk.approve" for capability in user.capabilities
        )
