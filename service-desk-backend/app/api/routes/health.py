from fastapi import APIRouter, Response

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


@router.get("/metrics")
def metrics() -> Response:
    payload = "\n".join(
        [
            "# HELP service_desk_app_info Static Service Desk application info.",
            "# TYPE service_desk_app_info gauge",
            'service_desk_app_info{service="service_desk"} 1',
            "",
        ]
    )
    return Response(content=payload, media_type="text/plain; version=0.0.4")
