from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class IncomingFile:
    file_name: str
    content_type: str | None
    read_chunk: Callable[[int], Awaitable[bytes]]


@dataclass(frozen=True, slots=True)
class FileDownload:
    content_type: str
    file_name: str
    source: BinaryIO | None = None


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    size_bytes: int
    checksum: str


class LocalFilesystemStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if self.root != candidate and self.root not in candidate.parents:
            raise ValueError("Storage key escapes its module root")
        return candidate

    def put(self, key: str, source: BinaryIO) -> str:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        with target.open("wb") as destination:
            while chunk := source.read(64 * 1024):
                digest.update(chunk)
                destination.write(chunk)
        return digest.hexdigest()

    def get(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def iter_keys(self, prefix: str = "") -> Iterable[str]:
        start = self._path(prefix) if prefix else self.root
        if not start.exists():
            return ()
        if start.is_file():
            return (start.relative_to(self.root).as_posix(),)
        return (
            candidate.relative_to(self.root).as_posix()
            for candidate in start.rglob("*")
            if candidate.is_file()
        )

    def path_for(self, key: str) -> Path:
        return self._path(key)


def safe_file_name(value: str, *, fallback: str = "attachment") -> str:
    name = Path(value).name
    clean = re.sub(r"[\x00-\x1f\\/:*?\"<>|]+", "_", name).strip(". ")
    return clean[:255] or fallback


async def stream_incoming_file(
    file: IncomingFile,
    *,
    destination: Path,
    max_size_bytes: int,
    chunk_size: int = 64 * 1024,
) -> StoredObject:
    if max_size_bytes < 1:
        raise ValueError("max_size_bytes must be positive")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.upload-{os.urandom(8).hex()}")
    size_bytes = 0
    digest = hashlib.sha256()
    try:
        with temporary.open("xb") as target:
            while chunk := await file.read_chunk(chunk_size):
                size_bytes += len(chunk)
                if size_bytes > max_size_bytes:
                    raise ValueError("File exceeds the configured size limit")
                digest.update(chunk)
                target.write(chunk)
        if size_bytes == 0:
            raise ValueError("File is empty")
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return StoredObject(
        key=destination.name,
        size_bytes=size_bytes,
        checksum=digest.hexdigest(),
    )
