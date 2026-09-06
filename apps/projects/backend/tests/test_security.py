from uuid import uuid4

import pytest

from app.core.enums import UserRole
from app.core.security import decode_access_token
from conftest import platform_test_token
from platform_sdk.error_types import AuthenticationRequired


def test_access_token_is_verified_by_the_platform_verifier():
    subject = str(uuid4())
    principal = decode_access_token(platform_test_token(subject, UserRole.PLATFORM_ADMIN))

    assert principal.user_id == subject
    assert principal.has_permission("projects.manage_all")


def test_legacy_token_is_not_an_authentication_fallback():
    with pytest.raises(AuthenticationRequired, match="токен платформы"):
        decode_access_token("legacy-hs256-token")
