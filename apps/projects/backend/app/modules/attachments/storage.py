from __future__ import annotations

from functools import lru_cache

from platform_sdk.storage import (
    AntivirusScanner,
    ClamAvTcpScanner,
    LocalFilesystemStorage,
    NoopAntivirusScanner,
    ObjectStorage,
    S3CompatibleStorage,
)

from app.core.config import settings


@lru_cache(maxsize=1)
def object_storage() -> ObjectStorage:
    if settings.storage_backend == "local":
        return LocalFilesystemStorage(settings.uploads_dir)
    if settings.storage_backend == "s3":
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required for the s3 storage backend")
        return S3CompatibleStorage(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region_name,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
        )
    raise RuntimeError(f"Unsupported storage backend: {settings.storage_backend}")


@lru_cache(maxsize=1)
def antivirus_scanner() -> AntivirusScanner:
    if settings.antivirus_backend == "noop":
        return NoopAntivirusScanner()
    if settings.antivirus_backend == "clamav":
        return ClamAvTcpScanner(settings.clamav_host, settings.clamav_port)
    raise RuntimeError(f"Unsupported antivirus backend: {settings.antivirus_backend}")
