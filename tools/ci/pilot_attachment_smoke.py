"""Exercise a real pilot response attachment through the public gateway."""

from __future__ import annotations

import json
import sys
from email.message import Message
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:5173"
STATE = Path(".pilot-attachment-smoke.json")
CONTENTS = b"PROM pilot attachment survives container recreation\n"


def fetch(path: str, *, method: str = "GET", token: str | None = None,
          body: bytes | None = None, content_type: str | None = None,
          cookie: str | None = None) -> tuple[bytes, Message]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if content_type:
        headers["Content-Type"] = content_type
    if cookie:
        headers["Cookie"] = cookie
    request = Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            return response.read(), response.headers
    except HTTPError as exc:
        raise AssertionError(f"{method} {path}: HTTP {exc.code}: {exc.read().decode()}") from exc


def login(email: str) -> str:
    _, headers = fetch(
        "/api/access/v1/auth/pilot/login",
        method="POST",
        body=json.dumps({"email": email}).encode(),
        content_type="application/json",
    )
    cookies = SimpleCookie()
    for value in headers.get_all("Set-Cookie", []):
        cookies.load(value)
    # CI talks to the loopback HTTP port; Secure cookies are sent manually here.
    cookie_header = "; ".join(f"{key}={morsel.value}" for key, morsel in cookies.items())
    assert cookie_header
    raw, _ = fetch("/api/access/v1/session/token", cookie=cookie_header)
    return json.loads(raw)["access_token"]


def create() -> None:
    employee = login("pilot.employee01@utmn.ru")
    manager = login("pilot.pm01@utmn.ru")
    raw, _ = fetch("/api/projects/v1/projects", token=employee)
    projects = json.loads(raw)["items"]
    project = next(item for item in projects if item["title"] == "Карта образовательных инициатив")
    project_id = project["id"]
    raw, _ = fetch(
        f"/api/projects/v1/projects/{project_id}/responses",
        method="POST",
        token=employee,
        body=json.dumps({
            "full_name": "Сотрудник 1",
            "email": "pilot.employee01@utmn.ru",
            "comment": "Проверка сохранности вложения пилота",
            "competencies": "Аналитика данных, SQL",
        }).encode(),
        content_type="application/json",
    )
    response_id = json.loads(raw)["id"]
    boundary = "prom-pilot-smoke-boundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"pilot.txt\"\r\n"
        "Content-Type: text/plain\r\n\r\n"
    ).encode() + CONTENTS + f"\r\n--{boundary}--\r\n".encode()
    raw, _ = fetch(
        f"/api/projects/v1/projects/{project_id}/responses/{response_id}/attachments",
        method="POST", token=employee, body=body,
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    attachment_id = json.loads(raw)["id"]
    verify_download(attachment_id, manager)
    STATE.write_text(json.dumps({"response_id": response_id, "attachment_id": attachment_id}))
    print("Employee response uploaded; project manager downloaded its attachment")


def verify_download(attachment_id: str, token: str) -> None:
    raw, _ = fetch(f"/api/projects/v1/attachments/{attachment_id}", token=token)
    assert raw == CONTENTS


def verify() -> None:
    state = json.loads(STATE.read_text())
    employee = login("pilot.employee01@utmn.ru")
    manager = login("pilot.pm01@utmn.ru")
    raw, _ = fetch("/api/projects/v1/me/responses", token=employee)
    assert state["response_id"] in {item["id"] for item in json.loads(raw)["items"]}
    verify_download(state["attachment_id"], manager)
    print("Response and attachment survived Compose down/up and repeated pilot seed")


if __name__ == "__main__":
    if sys.argv[1:] == ["create"]:
        create()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("Usage: pilot_attachment_smoke.py {create|verify}")
