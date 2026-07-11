import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.core.enums import SERVICE_DESK_CAPABILITIES, ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def access_token(subject: str, *, secret: str | None = None) -> str:
    return jwt.encode(
        {"sub": subject, "exp": datetime.now(UTC) + timedelta(minutes=5)},
        secret or settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_service_desk_user(
    db_session_factory,
    *,
    identity_user_id: str | None = None,
    is_active: bool = True,
    access_type: ServiceDeskAccessType = ServiceDeskAccessType.MANAGER,
    capabilities: tuple[str, ...] = ("service_desk.access",),
) -> ServiceDeskUser:
    with db_session_factory() as db:
        user = ServiceDeskUser(
            identity_user_id=identity_user_id or str(uuid.uuid4()),
            email=f"{uuid.uuid4()}@utmn.ru",
            display_name="Тестовый пользователь",
            department="ШПИУ",
            position="Менеджер",
            access_type=access_type,
            is_active=is_active,
        )
        db.add(user)
        db.flush()
        for capability in capabilities:
            db.add(
                ServiceDeskUserCapability(
                    service_desk_user_id=user.id,
                    capability=capability,
                )
            )
        db.commit()
        db.refresh(user)
        return user


def test_me_returns_local_projection_and_capabilities(client, db_session_factory):
    identity_user_id = str(uuid.uuid4())
    user = create_service_desk_user(
        db_session_factory,
        identity_user_id=identity_user_id,
        capabilities=("service_desk.access", "service_desk.approve"),
    )

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token(identity_user_id)}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "identity_user_id": identity_user_id,
        "email": user.email,
        "display_name": "Тестовый пользователь",
        "department": "ШПИУ",
        "position": "Менеджер",
        "access_type": "manager",
        "is_active": True,
        "capabilities": ["service_desk.access", "service_desk.approve"],
        "created_at": user.created_at.isoformat().replace("+00:00", "Z"),
        "updated_at": user.updated_at.isoformat().replace("+00:00", "Z"),
    }

    capabilities = client.get(
        "/me/capabilities",
        headers={"Authorization": f"Bearer {access_token(identity_user_id)}"},
    )
    assert capabilities.status_code == 200
    assert capabilities.json() == {
        "capabilities": ["service_desk.access", "service_desk.approve"]
    }


def test_service_desk_admin_receives_all_capabilities(client, db_session_factory):
    identity_user_id = str(uuid.uuid4())
    create_service_desk_user(
        db_session_factory,
        identity_user_id=identity_user_id,
        access_type=ServiceDeskAccessType.SERVICE_DESK_ADMIN,
        capabilities=(),
    )

    response = client.get(
        "/me/capabilities",
        headers={"Authorization": f"Bearer {access_token(identity_user_id)}"},
    )

    assert response.status_code == 200
    assert response.json()["capabilities"] == list(SERVICE_DESK_CAPABILITIES)


def test_me_rejects_missing_invalid_unknown_and_inactive_access(client, db_session_factory):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer invalid"}).status_code == 401

    unknown = client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token(str(uuid.uuid4()))}"},
    )
    assert unknown.status_code == 403

    no_access_identity = str(uuid.uuid4())
    create_service_desk_user(
        db_session_factory,
        identity_user_id=no_access_identity,
        capabilities=(),
    )
    no_access = client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token(no_access_identity)}"},
    )
    assert no_access.status_code == 403

    identity_user_id = str(uuid.uuid4())
    create_service_desk_user(
        db_session_factory,
        identity_user_id=identity_user_id,
        is_active=False,
    )
    inactive = client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token(identity_user_id)}"},
    )
    assert inactive.status_code == 403


def test_user_options_are_safe_active_and_capability_filtered(client, db_session_factory):
    requester_identity = str(uuid.uuid4())
    create_service_desk_user(db_session_factory, identity_user_id=requester_identity)
    approver = create_service_desk_user(
        db_session_factory,
        capabilities=("service_desk.access", "service_desk.approve"),
    )
    inactive = create_service_desk_user(db_session_factory, is_active=False)

    response = client.get(
        "/users/options",
        headers={"Authorization": f"Bearer {access_token(requester_identity)}"},
    )
    assert response.status_code == 200
    assert inactive.id not in {item["id"] for item in response.json()}
    assert {"id", "display_name", "department", "position"} == set(response.json()[0])
    assert "capabilities" not in response.json()[0]

    approver_options = client.get(
        "/users/options?capability=service_desk.approve",
        headers={"Authorization": f"Bearer {access_token(requester_identity)}"},
    )
    assert approver_options.status_code == 200
    assert str(approver.id) in {item["id"] for item in approver_options.json()}
    assert str(inactive.id) not in {item["id"] for item in approver_options.json()}

    assert client.get("/users/options").status_code == 401
