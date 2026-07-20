from __future__ import annotations

import hashlib
import os
import re
import socket
import struct
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol


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
    signed_url: str | None = None


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    size_bytes: int
    checksum: str


class AntivirusScanner(Protocol):
    def scan(self, path: Path) -> str: ...


class NoopAntivirusScanner:
    """Explicit local-development scanner adapter.

    Production configuration can replace it with a ClamAV or vendor adapter
    without moving attachment authorization into the shared package.
    """

    def scan(self, path: Path) -> str:
        if not path.is_file():
            raise FileNotFoundError(path)
        return "clean"


class ClamAvTcpScanner:
    """Minimal ClamAV INSTREAM adapter with no product-policy knowledge."""

    def __init__(
        self,
        host: str = "clamav",
        port: int = 3310,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds

    def scan(self, path: Path) -> str:
        if not path.is_file():
            raise FileNotFoundError(path)
        with socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout_seconds,
        ) as connection:
            connection.sendall(b"zINSTREAM\0")
            with path.open("rb") as source:
                while chunk := source.read(64 * 1024):
                    connection.sendall(struct.pack(">I", len(chunk)))
                    connection.sendall(chunk)
            connection.sendall(struct.pack(">I", 0))
            response = connection.recv(4096).decode("utf-8", errors="replace")
        if response.endswith("OK\0") or response.rstrip("\0\r\n").endswith("OK"):
            return "clean"
        if "FOUND" in response:
            return "infected"
        raise RuntimeError(f"ClamAV scan failed: {response.rstrip()}")


class ObjectStorage(Protocol):
    def put(self, key: str, source: BinaryIO) -> str: ...
    def get(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def iter_keys(self, prefix: str = "") -> Iterable[str]: ...
    def signed_download_url(
        self,
        key: str,
        *,
        ttl_seconds: int,
        file_name: str,
        content_type: str,
    ) -> str | None: ...


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

    def signed_download_url(
        self,
        key: str,
        *,
        ttl_seconds: int,
        file_name: str,
        content_type: str,
    ) -> str | None:
        return None

    def path_for(self, key: str) -> Path:
        return self._path(key)


class S3CompatibleStorage:
    """S3-compatible object storage adapter backed by boto3."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        import boto3

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def put(self, key: str, source: BinaryIO) -> str:
        digest = hashlib.sha256()

        class HashingReader:
            def read(self, size: int = -1) -> bytes:
                chunk = source.read(size)
                digest.update(chunk)
                return chunk

        self.client.upload_fileobj(HashingReader(), self.bucket, key)
        return digest.hexdigest()

    def get(self, key: str) -> BinaryIO:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"]

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise
        return True

    def iter_keys(self, prefix: str = "") -> Iterable[str]:
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
        return (
            item["Key"]
            for page in pages
            for item in page.get("Contents", ())
        )

    def signed_download_url(
        self,
        key: str,
        *,
        ttl_seconds: int,
        file_name: str,
        content_type: str,
    ) -> str | None:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        disposition_name = safe_file_name(file_name)
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ResponseContentDisposition": (
                    f'attachment; filename="{disposition_name}"'
                ),
                "ResponseContentType": content_type,
            },
            ExpiresIn=ttl_seconds,
        )


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
