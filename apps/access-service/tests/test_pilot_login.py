from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response

from access_service.api.router import pilot_login, require_mock_provider
from access_service.api.schemas import PilotLoginInput
from access_service.bootstrap.config import AccessSettings
from access_service.infrastructure.identity import InternalTokenSigner, generate_private_key_pem


def make_request(environment: str) -> SimpleNamespace:
    config = {"environment": environment, "database_url": "sqlite+pysqlite:///:memory:"}
    if environment in {"pilot", "production"}:
        config.update(
            database_url="postgresql+psycopg://access:secret@db/access",
            token_issuer="https://pilot.example.edu/access",
            token_audiences="projects",
            jwt_private_key=generate_private_key_pem(),
            jwt_key_id="pilot-test-key",
        )
    settings = AccessSettings(**config)
    return SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(token_signer=InternalTokenSigner(settings))
        )
    )


def test_mock_login_is_available_only_in_development() -> None:
    require_mock_provider(make_request("development"))
    for environment in ("pilot", "production"):
        with pytest.raises(HTTPException) as error:
            require_mock_provider(make_request(environment))
        assert error.value.status_code == 404


@pytest.mark.parametrize("environment", ["development", "production"])
def test_pilot_login_endpoint_is_unavailable_outside_pilot(environment: str) -> None:
    with pytest.raises(HTTPException) as error:
        pilot_login(
            PilotLoginInput(email="pilot.admin01@utmn.ru"),
            make_request(environment),
            Response(),
            session=None,  # type: ignore[arg-type]
        )
    assert error.value.status_code == 404


@pytest.mark.parametrize("email", [
    "pilot.admin01@utmn.ru",
    "pilot.pm05@utmn.ru",
    "pilot.employee12@utmn.ru",
])
def test_pilot_login_accepts_pilot_account_shapes(email: str) -> None:
    assert PilotLoginInput(email=email).email == email


@pytest.mark.parametrize("email", [
    "admin@utmn.ru",
    "pilot.admin01@example.com",
    "pilot.pm1@utmn.ru",
])
def test_pilot_login_rejects_non_pilot_addresses(email: str) -> None:
    with pytest.raises(ValueError):
        PilotLoginInput(email=email)
