import uuid

from app.core.enums import ServiceDeskAccessType, ServiceDeskTicketStatus
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.tickets.models import ServiceDeskTicket


def create_comment_user(
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
            access_type=ServiceDeskAccessType.MANAGER,
            is_active=True,
        )
        db.add(user)
        db.flush()
        for capability in {"service_desk.access", *capabilities}:
            db.add(
                ServiceDeskUserCapability(
                    service_desk_user_id=user.id,
                    capability=capability,
                )
            )
        db.commit()
        return str(user.id)


def create_waiting_requester_ticket(client, db_session_factory) -> tuple[str, str, str]:
    requester_id = create_comment_user(db_session_factory, "comment-requester@utmn.ru")
    assignee_id = create_comment_user(
        db_session_factory,
        "comment-assignee@utmn.ru",
        capabilities=("service_desk.be_assignee",),
    )
    category = client.post("/admin/categories", json={"title": "Comments category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Comments service"},
    )
    version = client.post(
        f"/admin/services/{service.json()['id']}/versions",
        json={"system_settings": {"is_description_required": False}},
    )
    published = client.post(f"/admin/template-versions/{version.json()['id']}/publish")
    assert published.status_code == 200, published.text
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service.json()["id"],
            "requester_user_id": requester_id,
            "title": "Comments ticket",
        },
    )
    submitted = client.post(f"/tickets/{draft.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text
    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(submitted.json()["id"]))
        assert ticket is not None
        ticket.assignee_user_id = uuid.UUID(assignee_id)
        ticket.status = ServiceDeskTicketStatus.WAITING_REQUESTER
        db.commit()
    return submitted.json()["id"], requester_id, assignee_id


def test_public_and_internal_comments_have_separate_visibility_and_audit(
    client,
    db_session_factory,
    auth_headers_for_user,
):
    ticket_id, requester_id, assignee_id = create_waiting_requester_ticket(client, db_session_factory)
    manager_id = create_comment_user(
        db_session_factory,
        "comment-manager@utmn.ru",
        capabilities=("service_desk.view_all_tickets",),
    )
    requester_headers = auth_headers_for_user(requester_id)
    assignee_headers = auth_headers_for_user(assignee_id)
    manager_headers = auth_headers_for_user(manager_id)

    public = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "Добавляю уточнение по заявке."},
        headers=requester_headers,
    )
    assert public.status_code == 201, public.text
    assert public.json()["visibility"] == "public"

    after_reply = client.get(f"/tickets/{ticket_id}", headers=requester_headers)
    assert after_reply.status_code == 200, after_reply.text
    assert after_reply.json()["status"] == "in_progress"
    assert [item["event_type"] for item in after_reply.json()["history"]][-2:] == [
        "comment_added",
        "requester_replied",
    ]

    denied_internal = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "Скрытая заметка", "visibility": "internal"},
        headers=requester_headers,
    )
    assert denied_internal.status_code == 403

    internal = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "Внутренняя заметка исполнителя.", "visibility": "internal"},
        headers=assignee_headers,
    )
    assert internal.status_code == 201, internal.text
    internal_id = internal.json()["id"]

    requester_comments = client.get(f"/tickets/{ticket_id}/comments", headers=requester_headers)
    assert requester_comments.status_code == 200
    assert [comment["visibility"] for comment in requester_comments.json()] == ["public"]
    requester_ticket = client.get(f"/tickets/{ticket_id}", headers=requester_headers)
    assert [comment["visibility"] for comment in requester_ticket.json()["comments"]] == ["public"]
    assert not any(
        item["payload"].get("comment_id") == internal_id
        for item in requester_ticket.json()["history"]
    )

    manager_comments = client.get(f"/tickets/{ticket_id}/comments", headers=manager_headers)
    assert manager_comments.status_code == 200
    assert [comment["visibility"] for comment in manager_comments.json()] == ["public", "internal"]

    updated = client.patch(
        f"/tickets/{ticket_id}/comments/{internal_id}",
        json={"body": "Обновлённая внутренняя заметка."},
        headers=assignee_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["updated_at"] is not None

    deleted = client.delete(
        f"/tickets/{ticket_id}/comments/{internal_id}",
        headers=assignee_headers,
    )
    assert deleted.status_code == 204
    manager_after_delete = client.get(f"/tickets/{ticket_id}", headers=manager_headers)
    assert [comment["visibility"] for comment in manager_after_delete.json()["comments"]] == ["public"]
    assert [item["event_type"] for item in manager_after_delete.json()["history"]][-2:] == [
        "comment_updated",
        "comment_deleted",
    ]
