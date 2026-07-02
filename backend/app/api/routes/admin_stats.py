from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.modules.stats.schemas import AdminStats
from app.modules.stats.service import StatsService

router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])


@router.get("", response_model=AdminStats)
def get_admin_stats(_: AdminUser, db: DbSession) -> AdminStats:
    return StatsService(db).get_admin_stats()
