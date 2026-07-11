from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db
from app.modules.stats.schemas import StatsFilters
from app.modules.stats.service import StatsService

router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])
Filters = Annotated[StatsFilters, Depends()]


@router.get("/summary")
def summary(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).summary(actor, filters)


@router.get("/statuses")
def statuses(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).statuses(actor, filters)


@router.get("/services")
def services(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).entities(actor, filters, "services")


@router.get("/categories")
def categories(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).entities(actor, filters, "categories")


@router.get("/times")
def times(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).times(actor, filters)


@router.get("/sla")
def sla(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).sla(actor, filters)


@router.get("/backlog-aging")
def backlog(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).backlog(actor, filters)


@router.get("/assignees")
def assignees(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).assignees(actor, filters)


@router.get("/approvals")
def approvals(filters: Filters, actor: CurrentServiceDeskUser, db: Session = Depends(get_db)):
    return StatsService(db).approvals(actor, filters)
