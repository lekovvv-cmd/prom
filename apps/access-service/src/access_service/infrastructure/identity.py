from __future__ import annotations

import base64
import hashlib
import ipaddress
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from urllib.parse import urlencode

import httpx
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


class InternalTokenSigner:
    def __init__(self, settings: AccessSettings) -> None:
        private_key = settings.jwt_private_key
        if private_key is None:
            generated = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            private_key = generated.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode()
        loaded_private_key = serialization.load_pem_private_key(
            private_key.encode(),
            password=None,
        )
        if not isinstance(loaded_private_key, rsa.RSAPrivateKey):
            raise ValueError("Access token signing key must be RSA")
        self.private_key: rsa.RSAPrivateKey = loaded_private_key
        self.public_key: rsa.RSAPublicKey = loaded_private_key.public_key()
        self.settings = settings

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
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.settings.jwt_key_id},
        )

    def jwks(self) -> dict[str, list[dict[str, str]]]:
        numbers = self.public_key.public_numbers()

        def encode(value: int) -> str:
            size = (value.bit_length() + 7) // 8
            return (
                base64.urlsafe_b64encode(value.to_bytes(size, "big"))
                .rstrip(b"=")
                .decode()
            )

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self.settings.jwt_key_id,
                    "n": encode(numbers.n),
                    "e": encode(numbers.e),
                }
            ]
        }


def build_identity_provider(settings: AccessSettings) -> IdentityProvider:
    if settings.sso_provider == "oidc":
        return OidcIdentityProvider(settings)
    if settings.sso_provider == "trusted-header":
        return TrustedHeaderIdentityProvider(settings)
    return LocalMockIdentityProvider()
