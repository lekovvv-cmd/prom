from __future__ import annotations

from platform_sdk.storage import (
    AntivirusScanner,
    ClamAvTcpScanner,
    LocalFilesystemStorage,
    NoopAntivirusScanner,
    ObjectStorage,
    S3CompatibleStorage,
)

from app.core.config import settings


def object_storage() -> ObjectStorage:
    if settings.storage_backend in {"filesystem", "local"}:
        return LocalFilesystemStorage(settings.storage_dir)
    if settings.storage_backend == "s3":
        if not settings.s3_bucket:
            raise RuntimeError("SERVICE_DESK_S3_BUCKET is required for S3 storage")
        return S3CompatibleStorage(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint,
            region_name=settings.s3_region,
            access_key_id=settings.s3_access_key,
            secret_access_key=settings.s3_secret_key,
        )
    raise RuntimeError(f"Unsupported Service Desk storage backend: {settings.storage_backend}")


def antivirus_scanner() -> AntivirusScanner:
    if settings.antivirus_backend == "noop":
        return NoopAntivirusScanner()
    if settings.antivirus_backend == "clamav":
        return ClamAvTcpScanner(
            settings.clamav_host,
            settings.clamav_port,
            timeout_seconds=settings.clamav_timeout_seconds,
        )
    raise RuntimeError(
        f"Unsupported Service Desk antivirus backend: {settings.antivirus_backend}"
    )
