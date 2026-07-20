import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from platform_sdk.database import pool_metrics
from platform_sdk.observability import get_service_metrics
from platform_sdk.outbox import outbox_metrics
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import engine, pool_config
from app.modules.attachments.repository import AttachmentRepository
from app.modules.notifications.models import ServiceDeskNotificationOutbox

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive", "service": settings.service_code}


@router.get("/health/ready", response_model=None)
def ready(db: Session = Depends(get_db)) -> dict[str, object] | JSONResponse:
    marker: Path | None = None
    try:
        db.execute(text("SELECT 1"))
        storage = Path(settings.storage_dir)
        storage.mkdir(parents=True, exist_ok=True)
        marker = storage / f".readiness-{uuid.uuid4().hex}"
        marker.write_bytes(b"ok")
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": settings.service_code,
            },
        )
    finally:
        if marker is not None:
            marker.unlink(missing_ok=True)

    pool_snapshot = pool_metrics(engine, pool_config)
    outbox_snapshot = outbox_metrics(db, ServiceDeskNotificationOutbox)
    metrics = get_service_metrics(
        service="service-desk-backend",
        module="service-desk",
    )
    metrics.record_db_pool(pool_snapshot)
    metrics.record_outbox(outbox_snapshot)
    return {
        "status": "ready",
        "service": settings.service_code,
        "checks": {"database": "ok", "storage": "ok"},
        "database_pool": pool_snapshot,
        "outbox": outbox_snapshot,
        "attachments": {"status_counts": AttachmentRepository(db).status_counts()},
    }


@router.get("/api/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_code}
