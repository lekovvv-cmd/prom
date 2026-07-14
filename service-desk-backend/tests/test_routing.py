import uuid

from app.core.enums import ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def create_routing_user(
    db_session_factory,
    email: str,
    *,
    capabilities: tuple[str, ...] = (),
) -> str:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=str(uuid.uuid4()),
            email=email,
            display_name=email.split("@", 1)[0],
            access_type=ServiceDeskAccessType.SERVICE_DESK_MANAGER,
            is_active=True,
        )
        db.add(user)
        db.flush()
        for capability in {
            "service_desk.access",
            "service_desk.create_request",
            *capabilities,
        }:
            db.add(
                ServiceDeskUserCapability(
                    service_desk_user_id=user.id,
                    capability=capability,
                )
            )
        db.commit()
        return str(user.id)


def create_published_service(
    client,
    *,
    default_assignee_user_id: str | None = None,
    publish: bool = True,
) -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:8]
    category = client.post("/admin/categories", json={"title": f"Routing category {suffix}"})
    service_payload = {
        "category_id": category.json()["id"],
        "title": f"Routing service {suffix}",
    }
    if default_assignee_user_id:
        service_payload["default_assignee_user_id"] = default_assignee_user_id
    service = client.post("/admin/services", json=service_payload)
    assert service.status_code == 201, service.text
    version = client.post(f"/admin/services/{service.json()['id']}/versions")
    assert version.status_code == 201, version.text
    if publish:
        published = client.post(f"/admin/template-versions/{version.json()['id']}/publish")
        assert published.status_code == 200, published.text
    return service.json()["id"], version.json()["id"]


def create_draft(
    client,
    service_id: str,
    requester_headers: dict[str, str],
    *,
    priority: str,
    field_values=None,
):
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "title": "Routing ticket",
            "description": "Проверка маршрутизации заявки.",
            "priority": priority,
            "field_values": field_values or {},
        },
        headers=requester_headers,
    )
    assert draft.status_code == 201, draft.text
    return draft.json()


def test_routing_assigns_first_priority_match_and_preserves_snapshot(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    routing_admin_id = create_routing_user(
        db_session_factory,
        "routing-admin@utmn.ru",
        capabilities=("service_desk.manage_routing",),
    )
    requester_id = create_routing_user(db_session_factory, "routing-requester@utmn.ru")
    routed_assignee_id = create_routing_user(
        db_session_factory,
        "routed-assignee@utmn.ru",
        capabilities=("service_desk.be_assignee",),
    )
    lower_priority_assignee_id = create_routing_user(
        db_session_factory,
        "lower-priority-assignee@utmn.ru",
        capabilities=("service_desk.be_assignee",),
    )
    default_assignee_id = create_routing_user(
        db_session_factory,
        "routing-default-assignee@utmn.ru",
        capabilities=("service_desk.be_assignee",),
    )
    service_id, _ = create_published_service(
        client,
        default_assignee_user_id=default_assignee_id,
    )
    admin_headers = auth_headers_for_user(routing_admin_id)

    candidates = client.get("/admin/routing-rules/candidates", headers=admin_headers)
    assert candidates.status_code == 200, candidates.text
    assert {candidate["id"] for candidate in candidates.json()} >= {
        routed_assignee_id,
        lower_priority_assignee_id,
        default_assignee_id,
    }

    catalog_options = client.get("/admin/routing-rules/catalog-options", headers=admin_headers)
    assert catalog_options.status_code == 200, catalog_options.text
    catalog_service = next(item for item in catalog_options.json()["services"] if item["id"] == service_id)
    assert catalog_service["is_active"] is True
    assert catalog_service["category_id"] in {
        item["id"] for item in catalog_options.json()["categories"]
    }

    forbidden = client.post(
        "/admin/routing-rules",
        json={
            "name": "Forbidden rule",
            "conditions": [],
            "action": {"type": "assign_user", "user_id": routed_assignee_id},
        },
        headers=auth_headers_for_user(requester_id),
    )
    assert forbidden.status_code == 403
    assert client.get(
        "/admin/routing-rules/catalog-options",
        headers=auth_headers_for_user(requester_id),
    ).status_code == 403

    invalid_assignee_id = create_routing_user(db_session_factory, "ineligible@utmn.ru")
    invalid = client.post(
        "/admin/routing-rules",
        json={
            "name": "Invalid assignee",
            "conditions": [],
            "action": {"type": "assign_user", "user_id": invalid_assignee_id},
        },
        headers=admin_headers,
    )
    assert invalid.status_code == 422

    first_rule = client.post(
        "/admin/routing-rules",
        json={
            "name": "Critical routing",
            "priority": 10,
            "conditions": [
                {"field": "service_id", "operator": "equals", "value": service_id},
                {"field": "priority", "operator": "equals", "value": "critical"},
            ],
            "action": {"type": "assign_user", "user_id": routed_assignee_id},
        },
        headers=admin_headers,
    )
    assert first_rule.status_code == 201, first_rule.text

    second_rule = client.post(
        "/admin/routing-rules",
        json={
            "name": "Fallback routing",
            "priority": 20,
            "conditions": [{"field": "service_id", "operator": "equals", "value": service_id}],
            "action": {"type": "assign_user", "user_id": lower_priority_assignee_id},
        },
        headers=admin_headers,
    )
    assert second_rule.status_code == 201, second_rule.text

    requester_headers = auth_headers_for_user(requester_id)
    draft = create_draft(client, service_id, requester_headers, priority="critical")
    submitted = client.post(f"/tickets/{draft['id']}/submit", headers=requester_headers)
    assert submitted.status_code == 200, submitted.text
    payload = submitted.json()
    assert payload["status"] == "assigned"
    assert payload["assignee_user_id"] == routed_assignee_id
    assert payload["routing_snapshot"]["assignment_rule"]["id"] == first_rule.json()["id"]
    assert [item["outcome"] for item in payload["routing_snapshot"]["matched_rules"]] == [
        "assignment_selected",
        "assignment_skipped_by_higher_priority_rule",
    ]
    assert payload["history"][-1]["payload"]["assignment_source"] == "routing_rule"
    assert payload["history"][-1]["payload"]["routing_rule_id"] == first_rule.json()["id"]

    reordered = client.post(
        "/admin/routing-rules/reorder",
        json={"rule_ids": [second_rule.json()["id"], first_rule.json()["id"]]},
        headers=admin_headers,
    )
    assert reordered.status_code == 200, reordered.text
    assert [rule["id"] for rule in reordered.json()] == [
        second_rule.json()["id"],
        first_rule.json()["id"],
    ]

    deleted = client.delete(
        f"/admin/routing-rules/{second_rule.json()['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 204
    assert client.get("/admin/routing-rules", headers=admin_headers).json()[0]["id"] == first_rule.json()["id"]


def test_routing_field_value_can_set_priority_before_assignment(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    routing_admin_id = create_routing_user(
        db_session_factory,
        "field-routing-admin@utmn.ru",
        capabilities=("service_desk.manage_routing",),
    )
    requester_id = create_routing_user(db_session_factory, "field-routing-requester@utmn.ru")
    assignee_id = create_routing_user(
        db_session_factory,
        "field-routing-assignee@utmn.ru",
        capabilities=("service_desk.be_assignee",),
    )
    service_id, version_id = create_published_service(client, publish=False)
    field = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "room",
            "label": "Аудитория",
            "field_type": "text",
            "is_required": True,
        },
    )
    assert field.status_code == 201, field.text
    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text
    admin_headers = auth_headers_for_user(routing_admin_id)

    priority_rule = client.post(
        "/admin/routing-rules",
        json={
            "name": "Room 305 is critical",
            "priority": 10,
            "conditions": [
                {
                    "field": "field_value",
                    "field_key": "room",
                    "operator": "equals",
                    "value": "305",
                }
            ],
            "action": {"type": "set_priority", "priority": "critical"},
        },
        headers=admin_headers,
    )
    assert priority_rule.status_code == 201, priority_rule.text
    assignment_rule = client.post(
        "/admin/routing-rules",
        json={
            "name": "Critical field assignment",
            "priority": 20,
            "conditions": [{"field": "priority", "operator": "equals", "value": "critical"}],
            "action": {"type": "assign_user", "user_id": assignee_id},
        },
        headers=admin_headers,
    )
    assert assignment_rule.status_code == 201, assignment_rule.text

    draft = create_draft(
        client,
        service_id,
        auth_headers_for_user(requester_id),
        priority="medium",
        field_values={"room": "305"},
    )
    submitted = client.post(
        f"/tickets/{draft['id']}/submit",
        headers=auth_headers_for_user(requester_id),
    )
    assert submitted.status_code == 200, submitted.text
    payload = submitted.json()
    assert payload["priority"] == "critical"
    assert payload["assignee_user_id"] == assignee_id
    assert payload["routing_snapshot"]["assignment_rule"]["id"] == assignment_rule.json()["id"]
    assert [item["event_type"] for item in payload["history"]][-3:] == [
        "routing_priority_applied",
        "ticket_approved",
        "ticket_assigned",
    ]
