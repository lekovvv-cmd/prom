from __future__ import annotations

import base64
import hashlib
import ipaddress
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections.abc import Callable
from typing import Protocol
from urllib.parse import urlencode

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import SigningKey


@dataclass(frozen=True, slots=True)
class ExternalPrincipal:
    subject: str
    email: str
    display_name: str
    department: str | None = None
    return_url: str | None = None


class IdentityProvider(Protocol):
    def authenticate_request(self, request: Request) -> ExternalPrincipal | None: ...
    def build_login_redirect(self, return_url: str) -> str: ...
    def handle_callback(self, request: Request) -> ExternalPrincipal: ...
    def build_logout_redirect(self, return_url: str) -> str: ...


class LocalMockIdentityProvider:
    def authenticate_request(self, request: Request) -> ExternalPrincipal | None:
        return None

    def build_login_redirect(self, return_url: str) -> str:
        return f"/auth/mock/login?return_url={return_url}"

    def handle_callback(self, request: Request) -> ExternalPrincipal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the mock login endpoint",
        )

    def build_logout_redirect(self, return_url: str) -> str:
        return return_url


class TrustedHeaderIdentityProvider:
    def __init__(self, settings: AccessSettings) -> None:
        self.settings = settings

    def authenticate_request(self, request: Request) -> ExternalPrincipal | None:
        if not self.settings.trusted_headers_enabled:
            return None
        client_host = request.client.host if request.client else None
        if not client_host or not self._is_trusted(client_host):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Trusted identity headers are accepted only from configured "
                    "proxy networks"
                ),
            )
        subject = request.headers.get("X-Forwarded-User")
        email = request.headers.get("X-Forwarded-Email")
        name = request.headers.get("X-Forwarded-Name")
        if not subject or not email or not name:
            return None
        return ExternalPrincipal(
            subject=subject,
            email=email.lower(),
            display_name=name,
            department=request.headers.get("X-Forwarded-Department"),
        )

    def _is_trusted(self, client_host: str) -> bool:
        configured = [
            item.strip()
            for item in self.settings.trusted_proxy_networks.split(",")
            if item.strip()
        ]
        if not configured:
            return False
        address = ipaddress.ip_address(client_host)
        return any(
            address in ipaddress.ip_network(item, strict=False)
            for item in configured
        )

    def build_login_redirect(self, return_url: str) -> str:
        return return_url

    def handle_callback(self, request: Request) -> ExternalPrincipal:
        principal = self.authenticate_request(request)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Trusted identity headers are missing",
            )
        return principal

    def build_logout_redirect(self, return_url: str) -> str:
        return return_url


class OidcIdentityProvider:
    """OIDC authorization-code adapter, disabled until real settings exist."""

    def __init__(self, settings: AccessSettings) -> None:
        self.settings = settings
        self._discovery: dict[str, object] | None = None
        self._discovery_fetched_at = 0.0

    def _require_configured(self) -> tuple[str, str, str, str]:
        if not (
            self.settings.oidc_enabled
            and self.settings.oidc_issuer_url
            and self.settings.oidc_client_id
            and self.settings.oidc_client_secret
            and self.settings.oidc_redirect_uri
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC provider is not configured",
            )
        return (
            self.settings.oidc_issuer_url,
            self.settings.oidc_client_id,
            self.settings.oidc_client_secret,
            self.settings.oidc_redirect_uri,
        )

    def authenticate_request(self, request: Request) -> ExternalPrincipal | None:
        return None

    def build_login_redirect(self, return_url: str) -> str:
        _, client_id, client_secret, redirect_uri = self._require_configured()
        authorization_endpoint = self._discovery_document().get(
            "authorization_endpoint"
        )
        if not isinstance(authorization_endpoint, str):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC discovery has no authorization endpoint",
            )
        nonce = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(64)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        state_token = jwt.encode(
            {
                "return_url": self._safe_return_url(return_url),
                "nonce": nonce,
                "verifier": verifier,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
            },
            client_secret,
            algorithm="HS256",
        )
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": self.settings.oidc_scopes,
                "state": state_token,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{authorization_endpoint}?{query}"

    def handle_callback(self, request: Request) -> ExternalPrincipal:
        issuer, client_id, client_secret, redirect_uri = self._require_configured()
        code = request.query_params.get("code")
        state_token = request.query_params.get("state")
        if not code or not state_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OIDC callback is missing code or state",
            )
        try:
            state_claims = jwt.decode(
                state_token,
                client_secret,
                algorithms=["HS256"],
                options={"require": ["exp", "nonce", "verifier"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OIDC callback state is invalid",
            ) from exc

        document = self._discovery_document()
        token_endpoint = document.get("token_endpoint")
        jwks_uri = document.get("jwks_uri")
        if not isinstance(token_endpoint, str) or not isinstance(jwks_uri, str):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC discovery is incomplete",
            )
        try:
            response = httpx.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code_verifier": state_claims["verifier"],
                },
                headers={"Accept": "application/json"},
                timeout=httpx.Timeout(5.0, connect=2.0),
            )
            response.raise_for_status()
            token_response = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OIDC token exchange failed",
            ) from exc
        id_token = (
            token_response.get("id_token")
            if isinstance(token_response, dict)
            else None
        )
        if not isinstance(id_token, str):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OIDC token response has no ID token",
            )
        try:
            signing_key = jwt.PyJWKClient(
                jwks_uri,
                cache_jwk_set=True,
                lifespan=self.settings.oidc_jwks_cache_ttl_seconds,
            ).get_signing_key_from_jwt(id_token)
            audiences = {
                client_id,
                *(
                    item.strip()
                    for item in self.settings.oidc_allowed_audiences.split(",")
                    if item.strip()
                ),
            }
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=list(audiences),
                issuer=issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OIDC ID token is invalid",
            ) from exc
        if claims.get("nonce") != state_claims.get("nonce"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OIDC nonce mismatch",
            )
        subject = claims.get("sub")
        email = claims.get("email") or claims.get("preferred_username")
        display_name = claims.get("name") or claims.get("display_name") or email
        if not isinstance(subject, str) or not subject:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="OIDC identity is missing required profile claims",
            )
        if not isinstance(email, str) or not email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="OIDC identity is missing required profile claims",
            )
        if not isinstance(display_name, str) or not display_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="OIDC identity is missing required profile claims",
            )
        return ExternalPrincipal(
            subject=subject,
            email=email.lower(),
            display_name=display_name,
            department=(
                claims.get("department")
                if isinstance(claims.get("department"), str)
                else None
            ),
            return_url=self._safe_return_url(
                str(state_claims.get("return_url") or "/")
            ),
        )

    def build_logout_redirect(self, return_url: str) -> str:
        self._require_configured()
        endpoint = self._discovery_document().get("end_session_endpoint")
        safe_return_url = (
            self.settings.oidc_post_logout_redirect_uri
            or self._safe_return_url(return_url)
        )
        if not isinstance(endpoint, str):
            return safe_return_url
        return (
            f"{endpoint}?"
            f"{urlencode({'post_logout_redirect_uri': safe_return_url})}"
        )

    def _discovery_document(self) -> dict[str, object]:
        issuer, _, _, _ = self._require_configured()
        now = time.monotonic()
        if (
            self._discovery is not None
            and now - self._discovery_fetched_at
            <= self.settings.oidc_jwks_cache_ttl_seconds
        ):
            return self._discovery
        issuer = issuer.rstrip("/")
        try:
            response = httpx.get(
                f"{issuer}/.well-known/openid-configuration",
                headers={"Accept": "application/json"},
                timeout=httpx.Timeout(5.0, connect=2.0),
            )
            response.raise_for_status()
            document = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC discovery is unavailable",
            ) from exc
        if (
            not isinstance(document, dict)
            or document.get("issuer") != self.settings.oidc_issuer_url
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC discovery issuer mismatch",
            )
        self._discovery = document
        self._discovery_fetched_at = time.monotonic()
        return document

    @staticmethod
    def _safe_return_url(return_url: str) -> str:
        if return_url.startswith("/") and not return_url.startswith("//"):
            return return_url
        return "/"


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
            "aud": list(self.settings.token_audience_values),
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


def build_identity_provider(settings: AccessSettings) -> IdentityProvider:
    if settings.sso_provider == "oidc":
        return OidcIdentityProvider(settings)
    if settings.sso_provider == "trusted-header":
        return TrustedHeaderIdentityProvider(settings)
    return LocalMockIdentityProvider()
