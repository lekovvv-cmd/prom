from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections.abc import Callable

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import SigningKey


@dataclass(frozen=True, slots=True)
class SigningKeyMaterial:
    kid: str
    private_key: rsa.RSAPrivateKey | None
    public_key: rsa.RSAPublicKey


def generate_private_key_pem() -> str:
    generated = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return generated.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def load_key_material(
    *,
    kid: str,
    private_key_pem: str | None,
    public_key_pem: str | None = None,
) -> SigningKeyMaterial:
    private_key: rsa.RSAPrivateKey | None = None
    if private_key_pem is not None:
        loaded_private = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
        )
        if not isinstance(loaded_private, rsa.RSAPrivateKey):
            raise ValueError("Access token signing key must be RSA")
        private_key = loaded_private
        public_key = loaded_private.public_key()
    elif public_key_pem is not None:
        loaded_public = serialization.load_pem_public_key(public_key_pem.encode())
        if not isinstance(loaded_public, rsa.RSAPublicKey):
            raise ValueError("Access token verification key must be RSA")
        public_key = loaded_public
    else:
        raise ValueError("A private or public key is required")
    return SigningKeyMaterial(kid=kid, private_key=private_key, public_key=public_key)


def public_key_pem(key: rsa.RSAPublicKey) -> str:
    return key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


class DatabaseSigningKeyStore:
    def __init__(
        self,
        settings: AccessSettings,
        session_factory: Callable[[], Session],
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory

    @staticmethod
    def _lock_rotation(session: Session) -> None:
        if session.bind is not None and session.bind.dialect.name == "postgresql":
            session.execute(text("SELECT pg_advisory_xact_lock(1886355537)"))

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _ensure_active(self, session: Session) -> SigningKey:
        self._lock_rotation(session)
        active_keys = list(
            session.scalars(
                select(SigningKey)
                .where(SigningKey.status == "active")
                .with_for_update()
            ).all()
        )
        if len(active_keys) > 1:
            raise RuntimeError("Signing key ring has more than one active key")
        if active_keys:
            if active_keys[0].private_key_pem is None:
                raise RuntimeError("Active signing key has no private material")
            return active_keys[0]
        private_pem = self.settings.signing_private_key or generate_private_key_pem()
        material = load_key_material(
            kid=self.settings.jwt_key_id,
            private_key_pem=private_pem,
        )
        now = datetime.now(timezone.utc)
        active = SigningKey(
            kid=self.settings.jwt_key_id,
            private_key_pem=private_pem,
            public_key_pem=public_key_pem(material.public_key),
            status="active",
            activated_at=now,
        )
        session.add(active)
        session.flush()
        return active

    def active(self) -> SigningKeyMaterial:
        with self.session_factory() as session:
            active = self._ensure_active(session)
            session.commit()
            return load_key_material(
                kid=active.kid,
                private_key_pem=active.private_key_pem,
            )

    def verification_keys(self) -> list[SigningKeyMaterial]:
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            self._ensure_active(session)
            keys = list(
                session.scalars(
                    select(SigningKey)
                    .where(
                        SigningKey.status.in_(["active", "verify_only"]),
                    )
                    .order_by(SigningKey.activated_at.desc(), SigningKey.created_at.desc())
                ).all()
            )
            result: list[SigningKeyMaterial] = []
            for key in keys:
                if (
                    key.status == "verify_only"
                    and key.verify_until is not None
                    and self._as_utc(key.verify_until) <= now
                ):
                    key.status = "retired"
                    key.retired_at = now
                    continue
                result.append(
                    load_key_material(
                        kid=key.kid,
                        private_key_pem=None,
                        public_key_pem=key.public_key_pem,
                    )
                )
            session.commit()
            return result

    def rotate(self, *, kid: str, private_key_pem: str | None = None) -> None:
        if not kid.strip():
            raise ValueError("Signing key id is required")
        private_pem = private_key_pem or generate_private_key_pem()
        material = load_key_material(kid=kid, private_key_pem=private_pem)
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            active = self._ensure_active(session)
            if active.kid == kid:
                raise ValueError("The requested signing key is already active")
            if session.scalar(select(SigningKey.id).where(SigningKey.kid == kid)):
                raise ValueError("Signing key id already exists")
            active.status = "verify_only"
            active.private_key_pem = None
            active.verify_until = now + timedelta(
                seconds=self.settings.jwt_rotation_overlap_seconds
            )
            session.add(
                SigningKey(
                    kid=kid,
                    private_key_pem=private_pem,
                    public_key_pem=public_key_pem(material.public_key),
                    status="active",
                    activated_at=now,
                )
            )
            session.commit()

    def retire_expired(self, *, now: datetime | None = None) -> int:
        current_time = now or datetime.now(timezone.utc)
        with self.session_factory() as session:
            keys = list(
                session.scalars(
                    select(SigningKey).where(
                        SigningKey.status == "verify_only",
                        SigningKey.verify_until.is_not(None),
                        SigningKey.verify_until <= current_time,
                    )
                ).all()
            )
            for key in keys:
                key.status = "retired"
                key.retired_at = current_time
            session.commit()
            return len(keys)


class InternalTokenSigner:
    def __init__(
        self,
        settings: AccessSettings,
        key_store: DatabaseSigningKeyStore | None = None,
    ) -> None:
        self.settings = settings
        self.key_store = key_store
        self._memory_key: SigningKeyMaterial | None = None
        if key_store is None:
            private_key = settings.signing_private_key or generate_private_key_pem()
            self._memory_key = load_key_material(
                kid=settings.jwt_key_id,
                private_key_pem=private_key,
            )

    @property
    def private_key(self) -> rsa.RSAPrivateKey:
        material = self._active()
        if material.private_key is None:
            raise RuntimeError("Active signing key has no private material")
        return material.private_key

    @property
    def public_key(self) -> rsa.RSAPublicKey:
        return self._active().public_key

    def _active(self) -> SigningKeyMaterial:
        if self.key_store is not None:
            return self.key_store.active()
        if self._memory_key is None:
            raise RuntimeError("Signing key is unavailable")
        return self._memory_key

    def _verification_keys(self) -> list[SigningKeyMaterial]:
        if self.key_store is not None:
            return self.key_store.verification_keys()
        return [self._active()]

    def issue(
        self,
        *,
        user_id: str,
        external_subject: str | None,
        email: str,
        display_name: str,
        permissions: set[str],
        session_version: int,
        audiences: list[str] | None = None,
        correlation_id: str | None = None,
    ) -> str:
        active = self._active()
        if active.private_key is None:
            raise RuntimeError("Active signing key has no private material")
        now = datetime.now(timezone.utc)
        claims: dict[str, object] = {
            "iss": self.settings.token_issuer,
            "sub": user_id,
            "external_sub": external_subject,
            "email": email,
            "display_name": display_name,
            "aud": audiences or list(self.settings.token_audience_values),
            "permissions": sorted(permissions),
            "sv": session_version,
            "iat": now,
            "exp": now + timedelta(seconds=self.settings.token_ttl_seconds),
            "jti": str(uuid.uuid4()),
        }
        if correlation_id:
            claims["cid"] = correlation_id
        return jwt.encode(
            claims,
            active.private_key,
            algorithm="RS256",
            headers={"kid": active.kid},
        )

    def verify(self, token: str, *, audience: str | list[str]) -> dict[str, object]:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise jwt.InvalidTokenError("Token has no signing key id")
        keys = {key.kid: key for key in self._verification_keys()}
        key = keys.get(kid)
        if key is None:
            raise jwt.InvalidTokenError("Unknown signing key id")
        return jwt.decode(
            token,
            key.public_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=self.settings.token_issuer,
            options={"require": ["exp", "iat", "sub", "jti", "sv"]},
        )

    def jwks(self) -> dict[str, list[dict[str, str]]]:
        def encode(value: int) -> str:
            size = (value.bit_length() + 7) // 8
            return (
                base64.urlsafe_b64encode(value.to_bytes(size, "big"))
                .rstrip(b"=")
                .decode()
            )

        keys: list[dict[str, str]] = []
        for material in self._verification_keys():
            numbers = material.public_key.public_numbers()
            keys.append(
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": material.kid,
                    "n": encode(numbers.n),
                    "e": encode(numbers.e),
                }
            )
        return {"keys": keys}
