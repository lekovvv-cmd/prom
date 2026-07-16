from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, Request, status


@dataclass(frozen=True, slots=True)
class CurrentPrincipal:
    """Verified platform identity delivered to a product module.

    This type intentionally contains no module business roles.  Product
    services combine generic permissions with their own object policy checks.
    """

    user_id: str
    external_subject: str | None
    email: str | None
    permissions: frozenset[str]
    audiences: frozenset[str]
    token_id: str | None = None

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "platform.admin" in self.permissions


def principal_from_claims(claims: dict[str, object]) -> CurrentPrincipal:
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("A platform token must contain a subject")
    permissions = claims.get("permissions", [])
    audience = claims.get("aud", [])
    return CurrentPrincipal(
        user_id=subject,
        external_subject=claims.get("external_sub") if isinstance(claims.get("external_sub"), str) else None,
        email=claims.get("email") if isinstance(claims.get("email"), str) else None,
        permissions=frozenset(item for item in permissions if isinstance(item, str)),
        audiences=frozenset([audience] if isinstance(audience, str) else (item for item in audience if isinstance(item, str))),
        token_id=claims.get("jti") if isinstance(claims.get("jti"), str) else None,
    )


def decode_internal_token(
    token: str,
    *,
    public_key: str,
    audience: str,
    issuer: str = "prom-access",
    algorithms: tuple[str, ...] = ("RS256", "ES256"),
) -> CurrentPrincipal:
    claims = jwt.decode(
        token,
        public_key,
        algorithms=list(algorithms),
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "sub", "jti"]},
    )
    return principal_from_claims(claims)


PrincipalResolver = Callable[[Request], CurrentPrincipal]


def require_permission(permission: str):
    def dependency(request: Request) -> CurrentPrincipal:
        resolver = getattr(request.app.state, "principal_resolver", None)
        if resolver is None:
            raise RuntimeError("The application has no platform principal resolver")
        principal = resolver(request)
        if not principal.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return principal

    return dependency


CurrentPrincipalDependency = Annotated[CurrentPrincipal, Depends(require_permission("platform.authenticated"))]

