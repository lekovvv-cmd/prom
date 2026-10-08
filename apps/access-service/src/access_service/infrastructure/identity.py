from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from access_service.bootstrap.config import AccessSettings


@dataclass(frozen=True, slots=True)
class SigningKeyMaterial:
    kid: str
    private_key: rsa.RSAPrivateKey
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
    private_key_pem: str,
) -> SigningKeyMaterial:
    loaded_private = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None
    )
    if not isinstance(loaded_private, rsa.RSAPrivateKey):
        raise ValueError("Access token signing key must be RSA")
    return SigningKeyMaterial(
        kid=kid,
        private_key=loaded_private,
        public_key=loaded_private.public_key(),
    )


class InternalTokenSigner:
    def __init__(self, settings: AccessSettings) -> None:
        self.settings = settings
        private_key = settings.signing_private_key or generate_private_key_pem()
        self._key = load_key_material(kid=settings.jwt_key_id, private_key_pem=private_key)

    @property
    def private_key(self) -> rsa.RSAPrivateKey:
        return self._key.private_key

    @property
    def public_key(self) -> rsa.RSAPublicKey:
        return self._key.public_key

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
        active = self._key
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
        if kid != self._key.kid:
            raise jwt.InvalidTokenError("Unknown signing key id")
        return jwt.decode(
            token,
            self._key.public_key,
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

        numbers = self._key.public_key.public_numbers()
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self._key.kid,
                    "n": encode(numbers.n),
                    "e": encode(numbers.e),
                }
            ]
        }
