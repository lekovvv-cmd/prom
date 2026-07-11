import asyncio
import io
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.enums import ServiceDeskAttachmentOwnerType, ServiceDeskTicketStatus
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.service import UPLOAD_CHUNK_SIZE, AttachmentService
from app.modules.tickets.models import ServiceDeskTicket

from test_comments import create_waiting_requester_ticket


def _ooxml_file(main_part: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("_rels/.rels", "<Relationships />")
        archive.writestr(main_part, "<document />")
    return buffer.getvalue()


class OversizedUpload:
    filename = "oversized.txt"
    content_type = "text/plain"

    def __init__(self, total_size: int) -> None:
        self.remaining = total_size
        self.bytes_returned = 0
        self.read_sizes: list[int] = []

    async def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        returned = min(size, self.remaining)
        self.remaining -= returned
        self.bytes_returned += returned
        return b"a" * returned


def test_ticket_and_internal_comment_attachments_use_private_storage_and_access(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    ticket_id, requester_id, assignee_id = create_waiting_requester_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
    )
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


def test_attachment_upload_rejects_invalid_content_and_accepts_ooxml(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    ticket_id, requester_id, _ = create_waiting_requester_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
    )
    requester_headers = auth_headers_for_user(requester_id)

    empty = client.post(
        f"/tickets/{ticket_id}/attachments",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=requester_headers,
    )
    assert empty.status_code == 422

    mismatched_content = client.post(
        f"/tickets/{ticket_id}/attachments",
        files={"file": ("fake.pdf", b"plain text", "application/pdf")},
        headers=requester_headers,
    )
    assert mismatched_content.status_code == 422

    spoofed_content_type = client.post(
        f"/tickets/{ticket_id}/attachments",
        files={"file": ("fake.png", b"not a png", "image/png")},
        headers=requester_headers,
    )
    assert spoofed_content_type.status_code == 422

    for file_name, content_type, main_part in (
        (
            "document.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "word/document.xml",
        ),
        (
            "workbook.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xl/workbook.xml",
        ),
        (
            "presentation.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "ppt/presentation.xml",
        ),
    ):
        uploaded = client.post(
            f"/tickets/{ticket_id}/attachments",
            files={"file": (file_name, _ooxml_file(main_part), content_type)},
            headers=requester_headers,
        )
        assert uploaded.status_code == 201, uploaded.text
        assert uploaded.json()["content_type"] == content_type


def test_comment_and_ticket_attachment_boundaries_for_foreign_and_closed_tickets(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    ticket_id, requester_id, assignee_id = create_waiting_requester_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
    )
    requester_headers = auth_headers_for_user(requester_id)
    assignee_headers = auth_headers_for_user(assignee_id)

    public_comment = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "Вложение к публичному комментарию"},
        headers=requester_headers,
    )
    assert public_comment.status_code == 201, public_comment.text
    comment_id = public_comment.json()["id"]

    foreign_upload = client.post(
        f"/tickets/{ticket_id}/comments/{comment_id}/attachments",
        files={"file": ("foreign.txt", b"foreign", "text/plain")},
        headers=assignee_headers,
    )
    assert foreign_upload.status_code == 403

    admin_upload = client.post(
        f"/tickets/{ticket_id}/comments/{comment_id}/attachments",
        files={"file": ("admin.txt", b"admin", "text/plain")},
        headers=client.admin_headers,
    )
    assert admin_upload.status_code == 201, admin_upload.text

    with db_session_factory() as db:
        ticket = db.get(ServiceDeskTicket, uuid.UUID(ticket_id))
        assert ticket is not None
        ticket.status = ServiceDeskTicketStatus.CLOSED
        db.commit()

    closed_ticket_upload = client.post(
        f"/tickets/{ticket_id}/attachments",
        files={"file": ("closed.txt", b"closed", "text/plain")},
        headers=requester_headers,
    )
    assert closed_ticket_upload.status_code == 409

    closed_comment_upload = client.post(
        f"/tickets/{ticket_id}/comments/{comment_id}/attachments",
        files={"file": ("closed-comment.txt", b"closed", "text/plain")},
        headers=requester_headers,
    )
    assert closed_comment_upload.status_code == 409


def test_oversized_attachment_stops_after_bounded_chunks_and_removes_partial_file(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "max_attachment_size_bytes", UPLOAD_CHUNK_SIZE + 1)
    ticket_id, requester_id, _ = create_waiting_requester_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
    )
    upload = OversizedUpload(total_size=10 * UPLOAD_CHUNK_SIZE)

    with db_session_factory() as db:
        service = AttachmentService(db)
        ticket = service._require_ticket(uuid.UUID(ticket_id))
        actor = ticket.requester
        with pytest.raises(HTTPException) as error:
            asyncio.run(
                service._store(
                    owner_type=ServiceDeskAttachmentOwnerType.TICKET,
                    owner_id=ticket.id,
                    ticket=ticket,
                    file=upload,
                    actor=actor,
                    comment_visibility=None,
                )
            )

    assert error.value.status_code == 422
    assert upload.read_sizes == [UPLOAD_CHUNK_SIZE, UPLOAD_CHUNK_SIZE]
    assert upload.bytes_returned == 2 * UPLOAD_CHUNK_SIZE
    assert upload.remaining > 0
    assert not list(Path(tmp_path).rglob("*.*"))


def test_attachment_upload_removes_physical_file_after_database_failure(
    client,
    db_session_factory,
    auth_headers_for_user,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    ticket_id, requester_id, _ = create_waiting_requester_ticket(
        client,
        db_session_factory,
        auth_headers_for_user,
    )

    def fail_add(self, attachment):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(AttachmentRepository, "add", fail_add)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        client.post(
            f"/tickets/{ticket_id}/attachments",
            files={"file": ("request.txt", b"ticket attachment", "text/plain")},
            headers=auth_headers_for_user(requester_id),
        )

    assert not list(Path(tmp_path).rglob("*.*"))
