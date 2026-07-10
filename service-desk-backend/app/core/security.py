import jwt

from app.core.config import settings


class InvalidAccessTokenError(ValueError):
    pass


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidAccessTokenError("Недействительный токен") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidAccessTokenError("Недействительный токен")
    return subject
