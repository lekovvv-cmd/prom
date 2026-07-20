from __future__ import annotations

import asyncio
import io

import pytest

from platform_sdk.storage import IncomingFile, LocalFilesystemStorage, safe_file_name, stream_incoming_file


def test_filesystem_storage_hashes_while_streaming(tmp_path) -> None:
    storage = LocalFilesystemStorage(tmp_path)

    checksum = storage.put("projects/project-1/file.bin", io.BytesIO(b"payload"))

    assert checksum == "239f59ed55e737c77147cf55ad0c1b030b6d7ee748a7426952f9b852d5a935e5"
    assert storage.get("projects/project-1/file.bin").read() == b"payload"
    assert list(storage.iter_keys("projects")) == ["projects/project-1/file.bin"]
    assert storage.signed_download_url(
        "projects/project-1/file.bin",
        ttl_seconds=60,
        file_name="file.bin",
        content_type="application/octet-stream",
    ) is None


def test_stream_incoming_file_enforces_limit_and_cleans_temporary_file(tmp_path) -> None:
    chunks = iter((b"1234", b"5678", b""))

    async def read_chunk(_: int) -> bytes:
        return next(chunks)

    with pytest.raises(ValueError, match="size limit"):
        asyncio.run(
            stream_incoming_file(
                IncomingFile("../../unsafe.txt", "text/plain", read_chunk),
                destination=tmp_path / "safe.txt",
                max_size_bytes=6,
            )
        )

    assert not list(tmp_path.iterdir())
    assert safe_file_name("../../unsafe.txt") == "unsafe.txt"
