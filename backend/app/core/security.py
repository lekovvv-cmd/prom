from datetime import UTC, datetime, timedelta
import re
from typing import Any

import jwt

from app.core.config import settings
from app.core.enums import UserRole
from app.core.exceptions import DomainError

UTMN_EMAIL_PATTERN = re.compile(r"^[^\s@]+@utmn\.ru$")


def create_access_token(
    subject: str,
    platform_role: UserRole,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "platform_role": platform_role.value,
        "exp": expire,
    }
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


def is_utmn_email(email: str) -> bool:
    return bool(UTMN_EMAIL_PATTERN.fullmatch(email.strip().lower()))


def ensure_utmn_email(email: str) -> str:
    normalized = email.strip().lower()
    if not is_utmn_email(normalized):
        raise DomainError("Разрешены только email на домене @utmn.ru")
    return normalized
