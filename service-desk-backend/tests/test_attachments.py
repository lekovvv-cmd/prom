from pathlib import Path

from app.core.config import settings

from test_comments import create_waiting_requester_ticket


def test_ticket_and_internal_comment_attachments_use_private_storage_and_access(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    ticket_id, requester_id, assignee_id = create_waiting_requester_ticket(client, db_session_factory)
    requester_headers = auth_headers_for_user(requester_id)
    assignee_headers = auth_headers_for_user(assignee_id)

    uploaded = client.post(
        f"/tickets/{ticket_id}/attachments",
        files={"file": ("request.txt", b"ticket attachment", "text/plain")},
        headers=requester_headers,
    )
    assert uploaded.status_code == 201, uploaded.text
    ticket_attachment = uploaded.json()
    assert ticket_attachment["owner_type"] == "service_desk_ticket"
    assert ticket_attachment["ticket_id"] == ticket_id
    assert ticket_attachment["file_name"] == "request.txt"
    assert ticket_attachment["size_bytes"] == len(b"ticket attachment")
    assert len(list(Path(tmp_path).rglob("*.txt"))) == 1

    listed = client.get(f"/tickets/{ticket_id}/attachments", headers=requester_headers)
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [ticket_attachment["id"]]

    unauthenticated_download = client.get(
        f"/tickets/{ticket_id}/attachments/{ticket_attachment['id']}/download"
    )
    assert unauthenticated_download.status_code == 401

    downloaded = client.get(
        f"/tickets/{ticket_id}/attachments/{ticket_attachment['id']}/download",
        headers=requester_headers,
    )
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == b"ticket attachment"
    assert "attachment; filename=\"request.txt\"" in downloaded.headers["content-disposition"]
    assert downloaded.headers["x-content-type-options"] == "nosniff"

    internal_comment = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "Internal attachment context", "visibility": "internal"},
        headers=assignee_headers,
    )
    assert internal_comment.status_code == 201, internal_comment.text
    comment_id = internal_comment.json()["id"]

    internal_upload = client.post(
        f"/tickets/{ticket_id}/comments/{comment_id}/attachments",
        files={"file": ("internal.pdf", b"%PDF-1.4", "application/pdf")},
        headers=assignee_headers,
    )
    assert internal_upload.status_code == 201, internal_upload.text
    assert internal_upload.json()["owner_type"] == "service_desk_comment"

    requester_internal_list = client.get(
        f"/tickets/{ticket_id}/comments/{comment_id}/attachments",
        headers=requester_headers,
    )
    assert requester_internal_list.status_code == 403
    requester_internal_download = client.get(
        f"/tickets/{ticket_id}/attachments/{internal_upload.json()['id']}/download",
        headers=requester_headers,
    )
    assert requester_internal_download.status_code == 403
    requester_ticket = client.get(f"/tickets/{ticket_id}", headers=requester_headers)
    assert not any(
        item["payload"].get("attachment_id") == internal_upload.json()["id"]
        for item in requester_ticket.json()["history"]
    )

    bad_mime = client.post(
        f"/tickets/{ticket_id}/attachments",
        files={"file": ("unexpected.txt", b"payload", "application/pdf")},
        headers=requester_headers,
    )
    assert bad_mime.status_code == 422
