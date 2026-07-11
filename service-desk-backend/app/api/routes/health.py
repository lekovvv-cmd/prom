from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive", "service": settings.service_code}


@router.get("/health/ready")
def ready() -> dict[str, object]:
    return {
        "status": "ready",
        "service": settings.service_code,
        "checks": {"application": "ok"},
    }


@router.get("/api/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_code}
