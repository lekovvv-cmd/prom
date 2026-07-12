import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

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

    return {
        "status": "ready",
        "service": settings.service_code,
        "checks": {"database": "ok", "storage": "ok"},
    }


@router.get("/api/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_code}
