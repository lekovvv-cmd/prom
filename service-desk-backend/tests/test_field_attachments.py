from pathlib import Path

from app.core.config import settings

from test_tickets import create_requester


def create_service_with_file_field(client) -> tuple[str, str]:
    category = client.post("/admin/categories", json={"title": "File field category"})
    assert category.status_code == 201, category.text
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "File field service"},
    )
    assert service.status_code == 201, service.text
    version = client.post(f"/admin/services/{service.json()['id']}/versions")
    assert version.status_code == 201, version.text
    version_id = version.json()["id"]
    file_field = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "supporting_document",
            "label": "Supporting document",
            "field_type": "file",
            "is_required": True,
            "position": 0,
            "validation": {"allowed_extensions": ["pdf"], "max_files": 1},
        },
    )
    assert file_field.status_code == 201, file_field.text
    text_field = client.post(
        f"/admin/template-versions/{version_id}/fields",
        json={
            "key": "reason",
            "label": "Reason",
            "field_type": "text",
            "position": 1,
        },
    )
    assert text_field.status_code == 201, text_field.text
    published = client.post(f"/admin/template-versions/{version_id}/publish")
    assert published.status_code == 200, published.text
    return service.json()["id"], version_id


def create_draft(client, service_id: str, requester_id: str) -> str:
    draft = client.post(
        "/tickets/drafts",
        json={
            "service_id": service_id,
            "requester_user_id": requester_id,
            "title": "Ticket with required file",
            "description": "A document must be attached.",
            "field_values": {
                "supporting_document": [{"name": "forged.pdf"}],
                "reason": "Verification",
            },
        },
    )
    assert draft.status_code == 201, draft.text
    return draft.json()["id"]


def test_dynamic_file_field_uses_private_attachment_metadata_on_submit(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    requester_id = create_requester(client, db_session_factory)
    other_user_id = create_requester(client, db_session_factory)
    service_id, _ = create_service_with_file_field(client)
    ticket_id = create_draft(client, service_id, requester_id)
    requester_headers = auth_headers_for_user(requester_id)

    submit_without_attachment = client.post(f"/tickets/{ticket_id}/submit")
    assert submit_without_attachment.status_code == 422
    assert submit_without_attachment.json()["detail"]["errors"] == [
        {"field_key": "supporting_document", "message": "Supporting document: Заполните обязательное поле"}
    ]

    wrong_actor = client.post(
        f"/tickets/{ticket_id}/fields/supporting_document/attachments",
        files={"file": ("document.pdf", b"%PDF-1.4", "application/pdf")},
        headers=auth_headers_for_user(other_user_id),
    )
    assert wrong_actor.status_code == 403

    non_file_field = client.post(
        f"/tickets/{ticket_id}/fields/reason/attachments",
        files={"file": ("document.pdf", b"%PDF-1.4", "application/pdf")},
        headers=requester_headers,
    )
    assert non_file_field.status_code == 422

    invalid_extension = client.post(
        f"/tickets/{ticket_id}/fields/supporting_document/attachments",
        files={"file": ("document.txt", b"plain text", "text/plain")},
        headers=requester_headers,
    )
    assert invalid_extension.status_code == 422

    uploaded = client.post(
        f"/tickets/{ticket_id}/fields/supporting_document/attachments",
        files={"file": ("document.pdf", b"%PDF-1.4", "application/pdf")},
        headers=requester_headers,
    )
    assert uploaded.status_code == 201, uploaded.text
    attachment = uploaded.json()
    assert attachment["owner_type"] == "service_desk_field_value"
    assert attachment["field_key"] == "supporting_document"
    assert len(list(Path(tmp_path).rglob("*.pdf"))) == 1

    listed = client.get(
        f"/tickets/{ticket_id}/fields/supporting_document/attachments",
        headers=requester_headers,
    )
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [attachment["id"]]

    second_file = client.post(
        f"/tickets/{ticket_id}/fields/supporting_document/attachments",
        files={"file": ("second.pdf", b"%PDF-1.4", "application/pdf")},
        headers=requester_headers,
    )
    assert second_file.status_code == 422

    submitted = client.post(f"/tickets/{ticket_id}/submit")
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["field_values"]["supporting_document"] == [
        {
            "id": attachment["id"],
            "name": "document.pdf",
            "content_type": "application/pdf",
            "size_bytes": len(b"%PDF-1.4"),
        }
    ]
    assert any(
        item["payload"].get("attachment_id") == attachment["id"]
        and item["payload"].get("field_key") == "supporting_document"
        for item in submitted.json()["history"]
    )

    after_submit = client.post(
        f"/tickets/{ticket_id}/fields/supporting_document/attachments",
        files={"file": ("late.pdf", b"%PDF-1.4", "application/pdf")},
        headers=requester_headers,
    )
    assert after_submit.status_code == 409
