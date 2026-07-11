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
    capabilities: tuple[str, ...] = (),
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
        assigned_capabilities = {"service_desk.access", *capabilities}
        if can_approve:
            assigned_capabilities.add("service_desk.approve")
        for capability in assigned_capabilities:
            db.add(
                ServiceDeskUserCapability(
                    service_desk_user_id=user.id,
                    capability=capability,
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


def test_submit_snapshots_published_approval_workflow(
    client,
    db_session_factory,
    auth_headers_for_user,
):
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
            "title": "Заявка со snapshot",
            "description": "Нужно согласовать заявку.",
        },
        headers=auth_headers_for_user(requester_id),
    )
    submitted = client.post(
        f"/tickets/{draft.json()['id']}/submit",
        headers=auth_headers_for_user(requester_id),
    )
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

    snapshot = client.get(
        f"/tickets/{payload['id']}/approvals",
        headers=auth_headers_for_user(requester_id),
    )
    assert snapshot.status_code == 200, snapshot.text
    assert [stage["title"] for stage in snapshot.json()] == ["Первый этап", "Второй этап"]


def test_default_assignee_is_applied_after_successful_approval(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    category = client.post("/admin/categories", json={"title": "Default assignment category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Default assignment service"},
    )
    default_assignee_id = create_approval_user(
        db_session_factory,
        "default-assignee@utmn.ru",
        can_approve=False,
        capabilities=("service_desk.be_assignee",),
    )
    version = client.post(
        f"/admin/services/{service.json()['id']}/versions",
        json={"default_assignee_user_id": default_assignee_id},
    )
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]
    assert version.json()["default_assignee_user_id"] == default_assignee_id

    configured = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={"approval_mode": "workflow", "name": "Default assignment workflow"},
    )
    workflow_id = configured.json()["workflow"]["id"]
    stage = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Согласование", "decision_rule": "any"},
    )
    stage_id = stage.json()["workflow"]["stages"][0]["id"]
    approver_id = create_approval_user(
        db_session_factory,
        "default-assignment-approver@utmn.ru",
        can_approve=True,
    )
    added = client.post(
        f"/admin/approval-stages/{stage_id}/approvers",
        json={"service_desk_user_id": approver_id},
    )
    assert added.status_code == 201, added.text
    assert client.post(f"/admin/template-versions/{version_id}/publish").status_code == 200

    requester_id = create_approval_user(
        db_session_factory,
        "default-assignment-requester@utmn.ru",
        can_approve=False,
    )
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "title": "Заявка с исполнителем по умолчанию",
            "description": "Нужно автоматическое назначение.",
        },
        headers=auth_headers_for_user(requester_id),
    )
    submitted = client.post(
        f"/tickets/{draft.json()['id']}/submit",
        headers=auth_headers_for_user(requester_id),
    )
    stage = submitted.json()["approval_stages"][0]
    approval_id = approval_id_for_actor(stage, approver_id)

    approved = client.post(
        f"/tickets/{submitted.json()['id']}/approvals/{approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_id),
    )
    assert approved.status_code == 200, approved.text
    payload = approved.json()
    assert payload["status"] == "assigned"
    assert payload["assignee_user_id"] == default_assignee_id
    assert [item["event_type"] for item in payload["history"]][-3:] == [
        "approval_approved",
        "ticket_approved",
        "ticket_assigned",
    ]
    assert payload["history"][-1]["payload"]["assignment_source"] == "default"


def test_service_default_assignee_is_used_without_version_override(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    default_assignee_id = create_approval_user(
        db_session_factory,
        "service-default-assignee@utmn.ru",
        can_approve=False,
        capabilities=("service_desk.be_assignee",),
    )
    category = client.post("/admin/categories", json={"title": "Service default category"})
    service = client.post(
        "/admin/services",
        json={
            "category_id": category.json()["id"],
            "title": "Service default service",
            "default_assignee_user_id": default_assignee_id,
        },
    )
    assert service.status_code == 201, service.text
    assert service.json()["default_assignee_user_id"] == default_assignee_id

    version = client.post(f"/admin/services/{service.json()['id']}/versions")
    assert version.status_code == 201, version.text
    assert version.json()["default_assignee_user_id"] is None
    published = client.post(f"/admin/template-versions/{version.json()['id']}/publish")
    assert published.status_code == 200, published.text

    requester_id = create_approval_user(
        db_session_factory,
        "service-default-requester@utmn.ru",
        can_approve=False,
    )
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "title": "Service default assignment",
            "description": "Проверка default assignment на уровне услуги.",
        },
        headers=auth_headers_for_user(requester_id),
    )
    assert draft.status_code == 201, draft.text

    submitted = client.post(
        f"/tickets/{draft.json()['id']}/submit",
        headers=auth_headers_for_user(requester_id),
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "assigned"
    assert submitted.json()["assignee_user_id"] == default_assignee_id
    assert submitted.json()["history"][-1]["event_type"] == "ticket_assigned"
    assert submitted.json()["history"][-1]["payload"]["assignment_source"] == "default"


def test_inactive_default_assignee_does_not_block_approval(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    category = client.post("/admin/categories", json={"title": "Inactive default category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Inactive default service"},
    )
    default_assignee_id = create_approval_user(
        db_session_factory,
        "inactive-default-assignee@utmn.ru",
        can_approve=False,
        capabilities=("service_desk.be_assignee",),
    )
    version = client.post(
        f"/admin/services/{service.json()['id']}/versions",
        json={"default_assignee_user_id": default_assignee_id},
    )
    version_id = version.json()["id"]
    configured = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={"approval_mode": "workflow", "name": "Inactive default workflow"},
    )
    workflow_id = configured.json()["workflow"]["id"]
    stage = client.post(
        f"/admin/approval-workflows/{workflow_id}/stages",
        json={"title": "Согласование", "decision_rule": "any"},
    )
    stage_id = stage.json()["workflow"]["stages"][0]["id"]
    approver_id = create_approval_user(
        db_session_factory,
        "inactive-default-approver@utmn.ru",
        can_approve=True,
    )
    client.post(
        f"/admin/approval-stages/{stage_id}/approvers",
        json={"service_desk_user_id": approver_id},
    )
    assert client.post(f"/admin/template-versions/{version_id}/publish").status_code == 200
    requester_id = create_approval_user(
        db_session_factory,
        "inactive-default-requester@utmn.ru",
        can_approve=False,
    )
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "title": "Заявка с неактивным исполнителем по умолчанию",
            "description": "Проверка пропуска назначения.",
        },
        headers=auth_headers_for_user(requester_id),
    )
    submitted = client.post(
        f"/tickets/{draft.json()['id']}/submit",
        headers=auth_headers_for_user(requester_id),
    )
    with db_session_factory() as db:
        default_assignee = db.get(ServiceDeskUser, uuid.UUID(default_assignee_id))
        assert default_assignee is not None
        default_assignee.is_active = False
        db.commit()

    approval_id = approval_id_for_actor(submitted.json()["approval_stages"][0], approver_id)
    approved = client.post(
        f"/tickets/{submitted.json()['id']}/approvals/{approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_id),
    )
    assert approved.status_code == 200, approved.text
    payload = approved.json()
    assert payload["status"] == "approved"
    assert payload["assignee_user_id"] is None
    assert payload["history"][-1]["event_type"] == "default_assignment_skipped"
    assert payload["history"][-1]["payload"]["assignment_source"] == "default"


def create_decision_ticket(
    client: TestClient,
    db_session_factory,
    auth_headers_for_user,
    stage_specs: list[tuple[str, int]],
) -> tuple[dict, list[list[str]], str]:
    suffix = uuid.uuid4().hex[:8]
    category = client.post("/admin/categories", json={"title": f"Decision category {suffix}"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": f"Decision service {suffix}"},
    )
    service_id = service.json()["id"]
    version = client.post(f"/admin/services/{service_id}/versions")
    version_id = version.json()["id"]
    configured = client.put(
        f"/admin/template-versions/{version_id}/approval-workflow",
        json={"approval_mode": "workflow", "name": f"Decision workflow {suffix}"},
    )
    workflow_id = configured.json()["workflow"]["id"]
    approver_ids: list[list[str]] = []

    for stage_index, (decision_rule, approver_count) in enumerate(stage_specs):
        created_stage = client.post(
            f"/admin/approval-workflows/{workflow_id}/stages",
            json={"title": f"Этап {stage_index + 1}", "decision_rule": decision_rule},
        )
        stage_id = created_stage.json()["workflow"]["stages"][-1]["id"]
        stage_approver_ids: list[str] = []
        for approver_index in range(approver_count):
            approver_id = create_approval_user(
                db_session_factory,
                f"decision-{suffix}-{stage_index}-{approver_index}@utmn.ru",
                can_approve=True,
            )
            added = client.post(
                f"/admin/approval-stages/{stage_id}/approvers",
                json={"service_desk_user_id": approver_id},
            )
            assert added.status_code == 201, added.text
            stage_approver_ids.append(approver_id)
        approver_ids.append(stage_approver_ids)

    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text
    requester_id = create_approval_user(
        db_session_factory,
        f"decision-requester-{suffix}@utmn.ru",
        can_approve=False,
    )
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "title": f"Decision ticket {suffix}",
            "description": "Заявка для проверки решений.",
        },
        headers=auth_headers_for_user(requester_id),
    )
    submitted = client.post(
        f"/tickets/{draft.json()['id']}/submit",
        headers=auth_headers_for_user(requester_id),
    )
    assert submitted.status_code == 200, submitted.text
    return submitted.json(), approver_ids, requester_id


def approval_id_for_actor(stage: dict, actor_user_id: str) -> str:
    return next(
        approval["id"]
        for approval in stage["approvals"]
        if approval["approver_user_id"] == actor_user_id
    )


def test_any_stage_completes_on_first_approval_and_skips_remaining(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    ticket, approver_ids, requester_id = create_decision_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
        [("any", 2)],
    )
    stage = ticket["approval_stages"][0]
    approval_id = approval_id_for_actor(stage, approver_ids[0][0])

    assert client.get(f"/tickets/{ticket['id']}").status_code == 401
    requester_view = client.get(
        f"/tickets/{ticket['id']}",
        headers=auth_headers_for_user(requester_id),
    )
    assert requester_view.status_code == 200
    assert requester_view.json()["allowed_actions"] == ["cancel"]

    approver_view = client.get(
        f"/tickets/{ticket['id']}",
        headers=auth_headers_for_user(approver_ids[0][0]),
    )
    assert approver_view.status_code == 200
    assert approver_view.json()["allowed_actions"] == ["approve", "reject"]
    assert approver_view.json()["service"]["title"].startswith("Decision service")
    assert approver_view.json()["approval_stages"][0]["approvals"][0][
        "approver_display_name"
    ].startswith("decision-")

    forbidden = client.post(
        f"/tickets/{ticket['id']}/approvals/{approval_id}/approve",
        json={},
        headers=auth_headers_for_user(requester_id),
    )
    assert forbidden.status_code == 403

    approved = client.post(
        f"/tickets/{ticket['id']}/approvals/{approval_id}/approve",
        json={"comment": "Согласовано"},
        headers=auth_headers_for_user(approver_ids[0][0]),
    )
    assert approved.status_code == 200, approved.text
    payload = approved.json()
    assert payload["status"] == "approved"
    assert payload["approval_stages"][0]["status"] == "approved"
    assert [item["status"] for item in payload["approval_stages"][0]["approvals"]] == [
        "approved",
        "skipped",
    ]
    assert [item["event_type"] for item in payload["history"]][-2:] == [
        "approval_approved",
        "ticket_approved",
    ]

    duplicate = client.post(
        f"/tickets/{ticket['id']}/approvals/{approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_ids[0][0]),
    )
    assert duplicate.status_code == 409


def test_all_stage_waits_for_every_approver(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    ticket, approver_ids, _ = create_decision_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
        [("all", 2)],
    )
    stage = ticket["approval_stages"][0]
    first_approval_id = approval_id_for_actor(stage, approver_ids[0][0])
    second_approval_id = approval_id_for_actor(stage, approver_ids[0][1])

    first = client.post(
        f"/tickets/{ticket['id']}/approvals/{first_approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_ids[0][0]),
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "pending_approval"
    assert first.json()["approval_stages"][0]["status"] == "pending"

    second = client.post(
        f"/tickets/{ticket['id']}/approvals/{second_approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_ids[0][1]),
    )
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "approved"
    assert second.json()["approval_stages"][0]["completed_at"] is not None


def test_multistage_progression_and_reject_skip_future_stages(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    ticket, approver_ids, _ = create_decision_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
        [("any", 1), ("all", 1), ("any", 1)],
    )
    stages = ticket["approval_stages"]
    first_approval_id = approval_id_for_actor(stages[0], approver_ids[0][0])
    second_approval_id = approval_id_for_actor(stages[1], approver_ids[1][0])

    before_activation = client.get(
        "/notifications",
        headers=auth_headers_for_user(approver_ids[1][0]),
    )
    assert before_activation.status_code == 200
    assert not any(
        item["event_type"] == "approval_requested"
        for item in before_activation.json()
    )

    premature = client.post(
        f"/tickets/{ticket['id']}/approvals/{second_approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_ids[1][0]),
    )
    assert premature.status_code == 409

    first = client.post(
        f"/tickets/{ticket['id']}/approvals/{first_approval_id}/approve",
        json={},
        headers=auth_headers_for_user(approver_ids[0][0]),
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "pending_approval"
    assert first.json()["approval_stages"][1]["started_at"] is not None
    assert first.json()["history"][-1]["event_type"] == "approval_stage_started"
    after_activation = client.get(
        "/notifications",
        headers=auth_headers_for_user(approver_ids[1][0]),
    )
    assert after_activation.status_code == 200
    approval_requests = [
        item
        for item in after_activation.json()
        if item["event_type"] == "approval_requested"
    ]
    assert len(approval_requests) == 1
    assert approval_requests[0]["ticket_id"] == ticket["id"]

    missing_reason = client.post(
        f"/tickets/{ticket['id']}/approvals/{second_approval_id}/reject",
        json={"comment": ""},
        headers=auth_headers_for_user(approver_ids[1][0]),
    )
    assert missing_reason.status_code == 422

    rejected = client.post(
        f"/tickets/{ticket['id']}/approvals/{second_approval_id}/reject",
        json={"comment": "Не хватает обоснования"},
        headers=auth_headers_for_user(approver_ids[1][0]),
    )
    assert rejected.status_code == 200, rejected.text
    payload = rejected.json()
    assert payload["status"] == "rejected"
    assert payload["rejected_at"] is not None
    assert [stage["status"] for stage in payload["approval_stages"]] == [
        "approved",
        "rejected",
        "skipped",
    ]
    assert payload["approval_stages"][2]["approvals"][0]["status"] == "skipped"
    assert payload["history"][-1]["event_type"] == "ticket_rejected"
    assert payload["history"][-1]["payload"]["comment"] == "Не хватает обоснования"
