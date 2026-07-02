from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings
from app.core.exceptions import DomainError


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise DomainError("Недействительный токен", status_code=401) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise DomainError("Недействительный токен", status_code=401)
    return subject


def ensure_utmn_email(email: str) -> str:
    normalized = email.strip().lower()
    if not normalized.endswith("@utmn.ru"):
        raise DomainError("Разрешены только email на домене @utmn.ru")
    return normalized
