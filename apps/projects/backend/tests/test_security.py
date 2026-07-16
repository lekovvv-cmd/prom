from datetime import timedelta
from uuid import uuid4

import jwt

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token


def test_access_token_contains_subject_and_platform_role():
    subject = str(uuid4())
    token = create_access_token(subject, UserRole.PLATFORM_ADMIN, timedelta(minutes=5))

    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

    assert payload["sub"] == subject
    assert payload["platform_role"] == "platform_admin"
    assert "exp" in payload
