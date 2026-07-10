import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentServiceDeskUser, get_db, require_service_desk_capability
from app.modules.routing import schemas
from app.modules.routing.service import RoutingService

router = APIRouter(
    prefix="/admin/routing-rules",
    tags=["admin-routing"],
    dependencies=[Depends(require_service_desk_capability("service_desk.manage_routing"))],
)


@router.get("", response_model=list[schemas.RoutingRuleRead])
def list_routing_rules(
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return RoutingService(db).list_rules(actor)


@router.get("/candidates", response_model=list[schemas.RoutingAssigneeRead])
def list_routing_candidates(
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return RoutingService(db).list_eligible_assignees(actor)


@router.post("", response_model=schemas.RoutingRuleRead, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    payload: schemas.RoutingRuleCreate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return RoutingService(db).create_rule(payload, actor)


@router.post("/reorder", response_model=list[schemas.RoutingRuleRead])
def reorder_routing_rules(
    payload: schemas.RoutingRulesReorder,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return RoutingService(db).reorder_rules(payload, actor)


@router.patch("/{rule_id}", response_model=schemas.RoutingRuleRead)
def update_routing_rule(
    rule_id: uuid.UUID,
    payload: schemas.RoutingRuleUpdate,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    return RoutingService(db).update_rule(rule_id, payload, actor)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_rule(
    rule_id: uuid.UUID,
    actor: CurrentServiceDeskUser,
    db: Session = Depends(get_db),
):
    RoutingService(db).delete_rule(rule_id, actor)
