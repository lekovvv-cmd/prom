from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from access_service.bootstrap.config import AccessSettings
from access_service.domain.models import BrowserSession, PlatformUser


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass(frozen=True, slots=True)
class BrowserSessionCredentials:
    session_secret: str
    csrf_token: str


class BrowserSessionManager:
    def __init__(self, settings: AccessSettings) -> None:
        self.settings = settings

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def create(
        self,
        session: Session,
        user: PlatformUser,
    ) -> BrowserSessionCredentials:
        now = datetime.now(timezone.utc)
        session_secret = secrets.token_urlsafe(48)
        csrf_token = secrets.token_urlsafe(32)
        session.add(
            BrowserSession(
                token_hash=self._hash(session_secret),
                csrf_hash=self._hash(csrf_token),
                user_id=user.id,
                session_version=user.session_version,
                last_seen_at=now,
                rotated_at=now,
                idle_expires_at=now
                + timedelta(seconds=self.settings.session_idle_ttl_seconds),
                absolute_expires_at=now
                + timedelta(seconds=self.settings.session_absolute_ttl_seconds),
            )
        )
        session.flush()
        return BrowserSessionCredentials(session_secret, csrf_token)

    def set_cookies(
        self,
        response: Response,
        credentials: BrowserSessionCredentials,
    ) -> None:
        response.set_cookie(
            self.settings.session_cookie_name,
            credentials.session_secret,
            max_age=self.settings.session_absolute_ttl_seconds,
            httponly=True,
            secure=self.settings.secure_cookies,
            samesite=self.settings.session_same_site,
            path="/",
        )
        response.set_cookie(
            self.settings.session_csrf_cookie_name,
            credentials.csrf_token,
            max_age=self.settings.session_absolute_ttl_seconds,
            httponly=False,
            secure=self.settings.secure_cookies,
            samesite=self.settings.session_same_site,
            path="/",
        )

    def clear_cookies(self, response: Response) -> None:
        response.delete_cookie(
            self.settings.session_cookie_name,
            httponly=True,
            secure=self.settings.secure_cookies,
            samesite=self.settings.session_same_site,
            path="/",
        )
        response.delete_cookie(
            self.settings.session_csrf_cookie_name,
            httponly=False,
            secure=self.settings.secure_cookies,
            samesite=self.settings.session_same_site,
            path="/",
        )

    def authenticate(
        self,
        request: Request,
        response: Response,
        session: Session,
    ) -> PlatformUser:
        session_secret = request.cookies.get(self.settings.session_cookie_name)
        if not session_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        browser_session = session.scalar(
            select(BrowserSession).where(
                BrowserSession.token_hash == self._hash(session_secret)
            )
        )
        if browser_session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Browser session is invalid",
            )
        now = datetime.now(timezone.utc)
        expired = (
            browser_session.revoked_at is not None
            or self._utc(browser_session.idle_expires_at) <= now
            or self._utc(browser_session.absolute_expires_at) <= now
        )
        user = session.get(PlatformUser, browser_session.user_id)
        revoked = (
            user is None
            or not user.is_active
            or browser_session.session_version != user.session_version
        )
        if expired or revoked:
            if browser_session.revoked_at is None:
                browser_session.revoked_at = now
                session.commit()
            self.clear_cookies(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Browser session expired or was revoked",
            )
        self._verify_csrf(request, browser_session)
        browser_session.last_seen_at = now
        browser_session.idle_expires_at = min(
            now + timedelta(seconds=self.settings.session_idle_ttl_seconds),
            self._utc(browser_session.absolute_expires_at),
        )
        if (
            now - self._utc(browser_session.rotated_at)
            >= timedelta(seconds=self.settings.session_rotation_seconds)
        ):
            rotated = BrowserSessionCredentials(
                session_secret=secrets.token_urlsafe(48),
                csrf_token=secrets.token_urlsafe(32),
            )
            browser_session.token_hash = self._hash(rotated.session_secret)
            browser_session.csrf_hash = self._hash(rotated.csrf_token)
            browser_session.rotated_at = now
            self.set_cookies(response, rotated)
        session.commit()
        return user

    def _verify_csrf(self, request: Request, browser_session: BrowserSession) -> None:
        if request.method.upper() in SAFE_METHODS:
            return
        cookie_token = request.cookies.get(self.settings.session_csrf_cookie_name, "")
        header_token = request.headers.get("X-CSRF-Token", "")
        valid = (
            bool(cookie_token)
            and bool(header_token)
            and hmac.compare_digest(cookie_token, header_token)
            and hmac.compare_digest(
                self._hash(header_token),
                browser_session.csrf_hash,
            )
        )
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed",
            )

    def revoke_current(self, request: Request, session: Session) -> None:
        session_secret = request.cookies.get(self.settings.session_cookie_name)
        if not session_secret:
            return
        browser_session = session.scalar(
            select(BrowserSession).where(
                BrowserSession.token_hash == self._hash(session_secret)
            )
        )
        if browser_session is not None and browser_session.revoked_at is None:
            browser_session.revoked_at = datetime.now(timezone.utc)
            session.flush()
