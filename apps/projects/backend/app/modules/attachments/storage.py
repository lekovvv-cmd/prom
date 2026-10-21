"""Attachment storage selected explicitly for the current deployment."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Protocol

from platform_sdk.storage import LocalFilesystemStorage
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.attachments.models import AttachmentBlob


class Storage(Protocol):
    def put(self, key: str, source: BinaryIO) -> str: ...
    def get(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def path_for(self, key: str) -> str | Path: ...


class DatabaseStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def put(self, key: str, source: BinaryIO) -> str:
        content = source.read()
        checksum = hashlib.sha256(content).hexdigest()
        self.db.add(AttachmentBlob(key=key, content=content))
        self.db.flush()
        return checksum

    def get(self, key: str) -> BinaryIO:
        blob = self.db.get(AttachmentBlob, key)
        if blob is None:
            raise FileNotFoundError(key)
        return BytesIO(blob.content)

    def delete(self, key: str) -> None:
        blob = self.db.get(AttachmentBlob, key)
        if blob is not None:
            self.db.delete(blob)
            self.db.flush()

    def exists(self, key: str) -> bool:
        return self.db.get(AttachmentBlob, key) is not None

    def path_for(self, key: str) -> str:
        return key


def create_storage(db: Session) -> Storage:
    if settings.storage_backend == "database":
        return DatabaseStorage(db)
    if settings.storage_backend == "local":
        return LocalFilesystemStorage(settings.uploads_dir)
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
