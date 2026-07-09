import uuid

from fastapi.testclient import TestClient

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.approvals.models import ServiceDeskApprovalStage


def create_template_version(client: TestClient) -> str:
    category = client.post("/admin/categories", json={"title": "Approval category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Approval service"},
    )
    version = client.post(f"/admin/services/{service.json()['id']}/versions")
    assert version.status_code == 201, version.text
    return version.json()["id"]


def create_approval_user(
    db_session_factory,
    email: str,
    *,
    can_approve: bool,
    access_type: ServiceDeskAccessType = ServiceDeskAccessType.MANAGER,
) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email=email,
            display_name=email.split("@", 1)[0],
            access_type=access_type,
            is_active=True,
        )
        db.add(user)
        db.flush()
        if can_approve:
            db.add(
                ServiceDeskUserCapability(
                    service_desk_user_id=user.id,
                    capability="service_desk.approve",
                )
            )
        db.commit()
        db.refresh(user)
        return str(user.id)


def test_admin_configures_multistage_approval_workflow(client, db_session_factory):
    version_id = create_template_version(client)
    initial = client.get(f"/admin/template-versions/{version_id}/approval-workflow")
    assert initial.status_code == 200
    assert initial.json()["approval_mode"] == "none"
    assert initial.json()["workflow"] is None

    configured = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={
            "approval_mode": "workflow",
            "name": "Согласование бронирования",
            "is_active": True,
        },
    )
    assert configured.status_code == 200, configured.text
    workflow_id = configured.json()["workflow"]["id"]

    first = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Руководитель подразделения", "decision_rule": "all"},
    )
    assert first.status_code == 201, first.text
    first_stage_id = first.json()["workflow"]["stages"][0]["id"]

    second = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Административный отдел", "decision_rule": "any"},
    )
    assert second.status_code == 201, second.text
    stages = second.json()["workflow"]["stages"]
    second_stage_id = next(stage["id"] for stage in stages if stage["title"] == "Административный отдел")

    no_capability_id = create_approval_user(
        db_session_factory,
        "no-approval-capability@utmn.ru",
        can_approve=False,
    )
    rejected_approver = client.post(
        f"/admin/approval-stages/{first_stage_id}/approvers",
        json={"service_desk_user_id": no_capability_id},
    )
    assert rejected_approver.status_code == 422

    approver_id = create_approval_user(
        db_session_factory,
        "approver@utmn.ru",
        can_approve=True,
    )
    admin_id = create_approval_user(
        db_session_factory,
        "sd-admin-approval@utmn.ru",
        can_approve=False,
        access_type=ServiceDeskAccessType.SERVICE_DESK_ADMIN,
    )
    first_approver = client.post(
        f"/admin/approval-stages/{first_stage_id}/approvers",
        json={"service_desk_user_id": approver_id},
    )
    assert first_approver.status_code == 201, first_approver.text
    first_approver_id = first_approver.json()["workflow"]["stages"][0]["approvers"][0]["id"]

    duplicate = client.post(
        f"/admin/approval-stages/{first_stage_id}/approvers",
        json={"service_desk_user_id": approver_id},
    )
    assert duplicate.status_code == 409

    second_approver = client.post(
        f"/admin/approval-stages/{second_stage_id}/approvers",
        json={"service_desk_user_id": admin_id},
    )
    assert second_approver.status_code == 201, second_approver.text

    removed = client.delete(f"/admin/approval-stage-approvers/{first_approver_id}")
    assert removed.status_code == 204
    restored = client.post(
        f"/admin/approval-stages/{first_stage_id}/approvers",
        json={"service_desk_user_id": approver_id},
    )
    assert restored.status_code == 201, restored.text

    reordered = client.post(
        f"/admin/approval-workflows/{workflow_id}/reorder-stages",
        json={"stage_ids": [second_stage_id, first_stage_id]},
    )
    assert reordered.status_code == 200, reordered.text
    assert [stage["id"] for stage in reordered.json()["workflow"]["stages"]] == [
        second_stage_id,
        first_stage_id,
    ]

    updated = client.patch(
        f"/admin/approval-stages/{first_stage_id}",
        json={"title": "Руководители подразделения", "decision_rule": "any"},
    )
    assert updated.status_code == 200, updated.text
    updated_stage = next(
        stage for stage in updated.json()["workflow"]["stages"] if stage["id"] == first_stage_id
    )
    assert updated_stage["decision_rule"] == "any"

    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text
    assert published.json()["approval_mode"] == "workflow"

    immutable = client.patch(
        f"/admin/approval-stages/{first_stage_id}",
        json={"title": "Нельзя изменить опубликованный workflow"},
    )
    assert immutable.status_code == 409


def test_workflow_template_cannot_publish_without_stages_and_approvers(client):
    version_id = create_template_version(client)
    configured = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={"approval_mode": "workflow", "name": "Неполный workflow"},
    )
    workflow_id = configured.json()["workflow"]["id"]

    no_stages = client.post(f"/admin/template-versions/{version_id}/publish")
    assert no_stages.status_code == 422
    assert no_stages.json()["detail"] == "Добавьте этап согласования"

    stage = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Обязательный этап", "decision_rule": "all"},
    )
    assert stage.status_code == 201, stage.text

    no_approvers = client.post(f"/admin/template-versions/{version_id}/publish")
    assert no_approvers.status_code == 422
    assert "Добавьте согласующего" in no_approvers.json()["detail"]

    disabled = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={"approval_mode": "none", "name": "Согласование не требуется"},
    )
    assert disabled.status_code == 200
    assert disabled.json()["workflow"]["is_active"] is False

    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text
    assert published.json()["approval_mode"] == "none"


def test_submit_snapshots_published_approval_workflow(client, db_session_factory):
    category = client.post("/admin/categories", json={"title": "Snapshot category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Snapshot service"},
    )
    service_id = service.json()["id"]
    version = client.post(f"/admin/services/{service_id}/versions")
    version_id = version.json()["id"]
    configured = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={"approval_mode": "workflow", "name": "Snapshot workflow"},
    )
    workflow_id = configured.json()["workflow"]["id"]

    first = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Первый этап", "decision_rule": "any"},
    )
    first_stage_id = first.json()["workflow"]["stages"][0]["id"]
    second = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Второй этап", "decision_rule": "all"},
    )
    second_stage_id = next(
        stage["id"]
        for stage in second.json()["workflow"]["stages"]
        if stage["title"] == "Второй этап"
    )

    first_approver_id = create_approval_user(
        db_session_factory,
        "snapshot-approver-1@utmn.ru",
        can_approve=True,
    )
    second_approver_id = create_approval_user(
        db_session_factory,
        "snapshot-approver-2@utmn.ru",
        can_approve=True,
    )
    client.post(
        f"/admin/approval-stages/{first_stage_id}/approvers",
        json={"service_desk_user_id": first_approver_id},
    )
    client.post(
        f"/admin/approval-stages/{second_stage_id}/approvers",
        json={"service_desk_user_id": second_approver_id},
    )
    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text

    requester_id = create_approval_user(
        db_session_factory,
        "snapshot-requester@utmn.ru",
        can_approve=False,
    )
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "requester_user_id": requester_id,
            "title": "Заявка со snapshot",
            "description": "Нужно согласовать заявку.",
        },
    )
    submitted = client.post(f"/tickets/{draft.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text
    payload = submitted.json()
    assert payload["status"] == "pending_approval"
    assert payload["approval_started_at"] is not None
    assert [stage["title"] for stage in payload["approval_stages"]] == ["Первый этап", "Второй этап"]
    assert payload["approval_stages"][0]["started_at"] is not None
    assert payload["approval_stages"][1]["started_at"] is None
    assert [stage["decision_rule"] for stage in payload["approval_stages"]] == ["any", "all"]
    assert [
        stage["approvals"][0]["approver_user_id"] for stage in payload["approval_stages"]
    ] == [first_approver_id, second_approver_id]
    assert [item["event_type"] for item in payload["history"]][-2:] == [
        "ticket_submitted",
        "approval_started",
    ]

    with db_session_factory() as db:
        source_stage = db.get(ServiceDeskApprovalStage, uuid.UUID(first_stage_id))
        assert source_stage is not None
        source_stage.title = "Изменённый исходный этап"
        db.commit()

    snapshot = client.get(f"/tickets/{payload['id']}/approvals")
    assert snapshot.status_code == 200, snapshot.text
    assert [stage["title"] for stage in snapshot.json()] == ["Первый этап", "Второй этап"]
