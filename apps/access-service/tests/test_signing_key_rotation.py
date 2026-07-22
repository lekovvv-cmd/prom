from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import Base, SigningKey
from access_service.infrastructure.identity import DatabaseSigningKeyStore, InternalTokenSigner


def issue(signer: InternalTokenSigner, user_id: str = "user-1") -> str:
    return signer.issue(
        user_id=user_id,
        external_subject="sso:user-1",
        email="user@utmn.ru",
        display_name="User",
        permissions={"projects.access"},
        session_version=1,
    )


def test_real_key_rotation_keeps_overlap_and_survives_restart(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'keys.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    settings = AccessSettings(
        database_url=str(engine.url),
        jwt_key_id="key-a",
        token_ttl_seconds=60,
        jwt_rotation_overlap_seconds=60,
    )
    store = DatabaseSigningKeyStore(settings, session_factory)
    signer = InternalTokenSigner(settings, store)

    token_a = issue(signer)
    assert jwt.get_unverified_header(token_a)["kid"] == "key-a"
    store.rotate(kid="key-b")
    token_b = issue(signer)
    assert jwt.get_unverified_header(token_b)["kid"] == "key-b"
    assert {key["kid"] for key in signer.jwks()["keys"]} == {"key-a", "key-b"}
    assert signer.verify(token_a, audience="projects")["sub"] == "user-1"
    assert signer.verify(token_b, audience="projects")["sub"] == "user-1"

    restarted = InternalTokenSigner(settings, DatabaseSigningKeyStore(settings, session_factory))
    assert jwt.get_unverified_header(issue(restarted))["kid"] == "key-b"
    with Session(engine) as session:
        assert session.scalar(
            select(func.count()).select_from(SigningKey).where(SigningKey.status == "active")
        ) == 1
        assert all("PRIVATE" not in key.public_key_pem for key in session.scalars(select(SigningKey)))

    store.retire_expired(now=datetime.now(timezone.utc) + timedelta(minutes=2))
    assert {key["kid"] for key in signer.jwks()["keys"]} == {"key-b"}
    try:
        signer.verify(token_a, audience="projects")
    except jwt.InvalidTokenError:
        pass
    else:
        raise AssertionError("Retired key A must fail closed")
    engine.dispose()


def test_unknown_or_missing_kid_fails_closed() -> None:
    settings = AccessSettings(
        database_url="sqlite+pysqlite:///:memory:",
        jwt_key_id="known",
    )
    signer = InternalTokenSigner(settings)
    token = issue(signer)
    claims = jwt.decode(token, options={"verify_signature": False})
    unknown = jwt.encode(
        claims,
        signer.private_key,
        algorithm="RS256",
        headers={"kid": "unknown"},
    )
    missing = jwt.encode(claims, signer.private_key, algorithm="RS256")

    for candidate in (unknown, missing):
        try:
            signer.verify(candidate, audience="projects")
        except jwt.InvalidTokenError:
            pass
        else:
            raise AssertionError("Token without a known kid must fail closed")

