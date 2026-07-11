import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentServiceDeskUser, DbSession
from app.core.enums import ServiceDeskPriority, ServiceDeskTicketStatus
from app.modules.workbench.schemas import (
    WorkbenchCounters,
    WorkbenchQuickView,
    WorkbenchSlaState,
    WorkbenchTicketPage,
    WorkbenchUserOption,
)
from app.modules.workbench.service import WorkbenchService


router = APIRouter(prefix="/workbench", tags=["workbench"])


@router.get("/tickets", response_model=WorkbenchTicketPage)
def list_workbench_tickets(
    db: DbSession,
    current_user: CurrentServiceDeskUser,
    status: ServiceDeskTicketStatus | None = None,
    assignee_user_id: uuid.UUID | None = None,
    requester_user_id: uuid.UUID | None = None,
    priority: ServiceDeskPriority | None = None,
    category_id: uuid.UUID | None = None,
    service_id: uuid.UUID | None = None,
    sla_state: WorkbenchSlaState | None = None,
    overdue: bool | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    q: Annotated[str | None, Query(max_length=255)] = None,
    quick_view: WorkbenchQuickView | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> WorkbenchTicketPage:
    return WorkbenchService(db).tickets(
        current_user,
        ticket_status=status,
        assignee_user_id=assignee_user_id,
        requester_user_id=requester_user_id,
        priority=priority,
        category_id=category_id,
        service_id=service_id,
        sla_state=sla_state,
        overdue=overdue,
        created_from=created_from,
        created_to=created_to,
        q=q,
        quick_view=quick_view,
        page=page,
        page_size=page_size,
    )


@router.get("/counters", response_model=WorkbenchCounters)
def get_workbench_counters(
    db: DbSession, current_user: CurrentServiceDeskUser
) -> WorkbenchCounters:
    return WorkbenchService(db).counters(current_user)


@router.get("/users", response_model=list[WorkbenchUserOption])
def get_workbench_users(
    db: DbSession,
    current_user: CurrentServiceDeskUser,
    eligible_assignees: bool = False,
) -> list[WorkbenchUserOption]:
    return WorkbenchService(db).user_options(
        current_user, eligible_assignees=eligible_assignees
    )
