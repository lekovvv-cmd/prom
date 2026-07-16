from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, Request, status

from access_service.bootstrap.config import AccessSettings


@dataclass(frozen=True, slots=True)
class ExternalPrincipal:
    subject: str
    email: str
    display_name: str
    department: str | None = None


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use the mock login endpoint")

    def build_logout_redirect(self, return_url: str) -> str:
        return return_url


class TrustedHeaderIdentityProvider:
    def __init__(self, settings: AccessSettings) -> None:
        self.settings = settings

    def authenticate_request(self, request: Request) -> ExternalPrincipal | None:
        if not self.settings.trusted_headers_enabled:
            return None
        subject = request.headers.get("X-Forwarded-User")
        email = request.headers.get("X-Forwarded-Email")
        name = request.headers.get("X-Forwarded-Name")
        if not all([subject, email, name]):
            return None
        return ExternalPrincipal(subject=subject, email=email, display_name=name, department=request.headers.get("X-Forwarded-Department"))

    def build_login_redirect(self, return_url: str) -> str:
        return return_url

    def handle_callback(self, request: Request) -> ExternalPrincipal:
        principal = self.authenticate_request(request)
        if principal is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Trusted identity headers are missing")
        return principal

    def build_logout_redirect(self, return_url: str) -> str:
        return return_url


class OidcIdentityProvider:
    """Configuration boundary for the future TюмГУ OIDC integration.

    It is deliberately disabled until issuer, client, and redirect parameters
    are supplied; no production endpoint is guessed in this repository.
    """

    def __init__(self, settings: AccessSettings) -> None:
        self.settings = settings

    def _disabled(self) -> None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OIDC provider is not configured")

    def authenticate_request(self, request: Request) -> ExternalPrincipal | None:
        return None

    def build_login_redirect(self, return_url: str) -> str:
        self._disabled()

    def handle_callback(self, request: Request) -> ExternalPrincipal:
        self._disabled()

    def build_logout_redirect(self, return_url: str) -> str:
        self._disabled()


class InternalTokenSigner:
    def __init__(self, settings: AccessSettings) -> None:
        private_key = settings.jwt_private_key
        if private_key is None:
            generated = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            private_key = generated.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode()
        self.private_key = private_key
        self.public_key = serialization.load_pem_private_key(private_key.encode(), password=None).public_key()
        self.settings = settings

    def issue(self, *, user_id: str, external_subject: str | None, email: str, permissions: set[str]) -> str:
        now = datetime.now(timezone.utc)
        claims = {
            "iss": self.settings.token_issuer,
            "sub": user_id,
            "external_sub": external_subject,
            "email": email,
            "aud": ["projects", "service-desk"],
            "permissions": sorted(permissions),
            "iat": now,
            "exp": now + timedelta(seconds=self.settings.token_ttl_seconds),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(claims, self.private_key, algorithm="RS256", headers={"kid": self.settings.jwt_key_id})

    def jwks(self) -> dict[str, list[dict[str, str]]]:
        numbers = self.public_key.public_numbers()

        def encode(value: int) -> str:
            size = (value.bit_length() + 7) // 8
            return base64.urlsafe_b64encode(value.to_bytes(size, "big")).rstrip(b"=").decode()

        return {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "kid": self.settings.jwt_key_id, "n": encode(numbers.n), "e": encode(numbers.e)}]}
