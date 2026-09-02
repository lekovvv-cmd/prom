from __future__ import annotations

import importlib
import json
import sys
import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from access_service.application.catalog import ensure_access_catalog
from access_service.bootstrap.app import create_app
from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import Base, PlatformUser, UserRoleAssignment
from access_service.infrastructure.database import get_session
from access_service.infrastructure.identity import InternalTokenSigner

GENERATOR_DIRECTORY = Path(__file__).parent
if str(GENERATOR_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(GENERATOR_DIRECTORY))
from create_module import _files  # noqa: E402


MODULE_ID = "audit-sample-module"
MODULE_PERMISSION = "audit_sample_module.access"


def _private_key() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


class _JwksHandler(BaseHTTPRequestHandler):
    jwks: dict[str, list[dict[str, str]]]

    def do_GET(self) -> None:  # noqa: N802
        payload = json.dumps(self.jwks).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _access_token(
    signer: InternalTokenSigner,
    *,
    user_id: str,
    permissions: set[str],
    session_version: int,
    audiences: list[str],
) -> str:
    return signer.issue(
        user_id=user_id,
        external_subject=None,
        email=f"{user_id}@utmn.ru",
        display_name=user_id,
        permissions=permissions,
        session_version=session_version,
        audiences=audiences,
    )


def _write_generated_backend(root: Path) -> Path:
    for relative, content in _files(MODULE_ID).items():
        if "backend" not in relative.parts:
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root / "apps" / MODULE_ID / "backend" / "src"


def test_generated_module_authorization_with_access_registration(tmp_path: Path, monkeypatch) -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with session_factory() as session:
        roles = ensure_access_catalog(session)
        admin = PlatformUser(id="admin", email="admin@utmn.ru", display_name="Admin")
        admin.assignments.append(UserRoleAssignment(role=roles["platform_admin"]))
        employee = PlatformUser(
            id="employee", email="employee@utmn.ru", display_name="Employee"
        )
        session.add_all([admin, employee])
        session.commit()

    private_key = _private_key()
    settings = AccessSettings(
        database_url="sqlite+pysqlite:///:memory:",
        jwt_private_key=private_key,
        jwt_key_id="generator-e2e",
    )
    signer = InternalTokenSigner(settings)
    access_app = create_app()
    access_app.state.token_signer = signer

    def session_dependency() -> Generator[Session]:
        with session_factory() as session:
            yield session

    access_app.dependency_overrides[get_session] = session_dependency
    admin_token = _access_token(
        signer,
        user_id="admin",
        permissions={"platform.admin"},
        session_version=1,
        audiences=["projects", "service-desk"],
    )
    access_client = TestClient(access_app)
    registered = access_client.post(
        "/api/v1/admin/modules",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"id": MODULE_ID, "title": "Audit Sample Module"},
    )
    assert registered.status_code == 201

    server = ThreadingHTTPServer(("127.0.0.1", 0), _JwksHandler)
    _JwksHandler.jwks = signer.jwks()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    source = _write_generated_backend(tmp_path)
    monkeypatch.setenv(
        "AUDIT_SAMPLE_MODULE_ACCESS_JWKS_URL",
        f"http://127.0.0.1:{server.server_port}/.well-known/jwks.json",
    )
    sys.path.insert(0, str(source))
    try:
        generated = importlib.import_module("audit_sample_module.bootstrap.app")
        generated_client = TestClient(generated.create_app())
        employee_token = _access_token(
            signer,
            user_id="employee",
            permissions=set(),
            session_version=1,
            audiences=["projects", "service-desk", MODULE_ID],
        )
        assert generated_client.get("/api/v1/me").status_code == 401
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": "Bearer malformed"}
        ).status_code == 401
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {employee_token}"}
        ).status_code == 403

        wrong_audience = _access_token(
            signer,
            user_id="employee",
            permissions={MODULE_PERMISSION},
            session_version=1,
            audiences=["projects"],
        )
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {wrong_audience}"}
        ).status_code == 401

        wrong_issuer_signer = InternalTokenSigner(
            AccessSettings(
                database_url="sqlite+pysqlite:///:memory:",
                token_issuer="wrong-access",
                jwt_private_key=private_key,
                jwt_key_id="generator-e2e",
            )
        )
        wrong_issuer = _access_token(
            wrong_issuer_signer,
            user_id="employee",
            permissions={MODULE_PERMISSION},
            session_version=1,
            audiences=["projects", "service-desk", MODULE_ID],
        )
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {wrong_issuer}"}
        ).status_code == 401

        forged = _access_token(
            InternalTokenSigner(
                AccessSettings(database_url="sqlite+pysqlite:///:memory:", jwt_key_id="forged")
            ),
            user_id="employee",
            permissions={MODULE_PERMISSION},
            session_version=1,
            audiences=["projects", "service-desk", MODULE_ID],
        )
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {forged}"}
        ).status_code == 401

        assert access_client.get(
            "/api/v1/me/modules", headers={"Authorization": f"Bearer {employee_token}"}
        ).json() == []
        role = access_client.post(
            "/api/v1/admin/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "code": "audit_reader",
                "title": "Audit reader",
                "module_id": MODULE_ID,
                "permissions": [MODULE_PERMISSION],
            },
        )
        assert role.status_code == 201
        assigned = access_client.put(
            "/api/v1/admin/users/employee/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role_codes": ["audit_reader"]},
        )
        assert assigned.status_code == 200
        assert assigned.json()["session_version"] == 2
        assert access_client.get(
            "/api/v1/me/modules", headers={"Authorization": f"Bearer {employee_token}"}
        ).status_code == 401

        renewed_employee = _access_token(
            signer,
            user_id="employee",
            permissions={MODULE_PERMISSION},
            session_version=2,
            audiences=["projects", "service-desk", MODULE_ID],
        )
        assert access_client.get(
            "/api/v1/me/modules",
            headers={"Authorization": f"Bearer {renewed_employee}"},
        ).json() == [{"id": MODULE_ID, "permissions": [MODULE_PERMISSION]}]
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {renewed_employee}"}
        ).json() == {"user_id": "employee", "module_id": MODULE_ID}

        renewed_admin = _access_token(
            signer,
            user_id="admin",
            permissions={"platform.admin"},
            session_version=1,
            audiences=[MODULE_ID],
        )
        assert generated_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {renewed_admin}"}
        ).status_code == 200
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        sys.path.remove(str(source))
        for module_name in list(sys.modules):
            if module_name == "audit_sample_module" or module_name.startswith("audit_sample_module."):
                sys.modules.pop(module_name)
        engine.dispose()
