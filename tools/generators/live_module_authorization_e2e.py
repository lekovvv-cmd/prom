"""Exercise a generated module against live Compose PostgreSQL services."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


BASE = "http://127.0.0.1:5173"
ACCESS = f"{BASE}/api/access/v1"
MODULE = "audit-sample-module"
PERMISSION = "audit_sample_module.access"
MODULE_API = f"{BASE}/api/{MODULE}/v1/me"


def request(method: str, url: str, *, payload: object | None = None, token: str | None = None) -> tuple[int, object]:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, body, headers, method), timeout=15) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def token(email: str) -> dict[str, object]:
    status, result = request("POST", f"{ACCESS}/auth/mock/token", payload={"email": email, "code": "000000"})
    assert status == 200, result
    assert isinstance(result, dict)
    return result


def main() -> int:
    admin = token("admin@utmn.ru")
    pre_registration_employee = token("employee@utmn.ru")
    admin_token = str(admin["access_token"])
    employee_id = str(pre_registration_employee["session"]["user"]["id"])

    status, result = request("POST", f"{ACCESS}/admin/modules", payload={"id": MODULE, "title": "Audit Sample Module"}, token=admin_token)
    assert status == 201, result
    status, modules = request("GET", f"{ACCESS}/admin/modules", token=admin_token)
    assert status == 200 and any(item["id"] == MODULE for item in modules), modules
    employee = token("employee@utmn.ru")
    employee_token = str(employee["access_token"])
    assert request("GET", f"{ACCESS}/me/modules", token=employee_token) == (200, [])
    assert request("GET", MODULE_API)[0] == 401
    assert request("GET", MODULE_API, token="malformed")[0] == 401
    assert request("GET", MODULE_API, token=str(pre_registration_employee["access_token"]))[0] == 401
    assert request("GET", MODULE_API, token=employee_token)[0] == 403

    status, role = request("POST", f"{ACCESS}/admin/roles", payload={"code": "audit_reader", "title": "Audit reader", "module_id": MODULE, "permissions": [PERMISSION]}, token=admin_token)
    assert status == 201, role
    status, assigned = request("PUT", f"{ACCESS}/admin/users/{employee_id}/roles", payload={"role_codes": ["audit_reader"]}, token=admin_token)
    assert status == 200 and assigned["session_version"] == 2, assigned
    assert request("GET", f"{ACCESS}/me/modules", token=employee_token)[0] == 401

    renewed = token("employee@utmn.ru")
    renewed_token = str(renewed["access_token"])
    status, modules = request("GET", f"{ACCESS}/me/modules", token=renewed_token)
    assert status == 200 and modules == [{"id": MODULE, "permissions": [PERMISSION]}], modules
    assert request("GET", MODULE_API, token=renewed_token)[0] == 200

    renewed_admin = token("admin@utmn.ru")
    assert request("GET", f"{ACCESS}/me/modules", token=str(renewed_admin["access_token"]))[0] == 200
    assert request("GET", MODULE_API, token=str(renewed_admin["access_token"]))[0] == 200
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError) as exc:
        print(f"Live generated-module authorization failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
