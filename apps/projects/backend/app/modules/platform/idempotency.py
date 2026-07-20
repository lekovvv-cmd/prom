from __future__ import annotations

import hashlib
import json
from typing import Any

from platform_sdk.error_types import ConflictDetected
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.platform.models import ProjectIdempotencyRecord


def request_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class IdempotencyStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def replay(
        self,
        *,
        scope: str,
        key: str | None,
        request_hash: str,
    ) -> tuple[int, dict[str, Any]] | None:
        if not key:
            return None
        record = self.db.scalar(
            select(ProjectIdempotencyRecord).where(
                ProjectIdempotencyRecord.scope == scope,
                ProjectIdempotencyRecord.idempotency_key == key,
            )
        )
        if record is None:
            return None
        if record.request_hash != request_hash:
            raise ConflictDetected(
                "Idempotency-Key уже использован для другого содержимого команды"
            )
        if record.response_status is None or record.response_body is None:
            raise ConflictDetected("Команда с таким Idempotency-Key ещё выполняется")
        return record.response_status, record.response_body

    def save(
        self,
        *,
        scope: str,
        key: str | None,
        request_hash: str,
        response_status: int,
        response_body: dict[str, Any],
    ) -> None:
        if not key:
            return
        self.db.add(
            ProjectIdempotencyRecord(
                scope=scope,
                idempotency_key=key,
                request_hash=request_hash,
                response_status=response_status,
                response_body=response_body,
            )
        )
        self.db.flush()
