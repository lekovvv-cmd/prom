from fastapi import APIRouter

from app.modules.competencies.schemas import CompetencyRead
from app.modules.competencies.service import CompetencyService

router = APIRouter(prefix="/competencies", tags=["competencies"])


@router.get("", response_model=list[CompetencyRead])
def list_competencies(search: str | None = None) -> list[CompetencyRead]:
    return CompetencyService().list(search)
