from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import ServiceDeskAccessType, ServiceDeskTicketAction
from app.modules.access.models import ServiceDeskUser
from app.modules.assignments.policy import AssigneePolicy
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.catalog.service import CatalogService
from app.modules.routing import schemas
from app.modules.routing.models import ServiceDeskRoutingRule
from app.modules.routing.repository import RoutingRuleRepository
from app.modules.tickets.lifecycle import TicketLifecycleService
from app.modules.tickets.models import ServiceDeskTicket, ServiceDeskTicketHistory
from app.modules.tickets.repository import TicketRepository


class RoutingService:
    def __init__(self, db: Session, ticket_repository: TicketRepository | None = None) -> None:
        self.db = db
        self.repository = RoutingRuleRepository(db)
        self.ticket_repository = ticket_repository or TicketRepository(db)
        self.lifecycle = TicketLifecycleService(self.ticket_repository)
        self.assignee_policy = AssigneePolicy(db)

    def list_rules(self, actor: ServiceDeskUser) -> list[ServiceDeskRoutingRule]:
        self._require_manage_routing(actor)
        return self.repository.list_rules()

    def list_eligible_assignees(self, actor: ServiceDeskUser) -> list[ServiceDeskUser]:
        self._require_manage_routing(actor)
        return self.assignee_policy.list_eligible_assignees()

    def list_catalog_options(
        self,
        actor: ServiceDeskUser,
    ) -> tuple[list[ServiceDeskCategory], list[ServiceDeskService]]:
        """Return active catalog entries without requiring catalog-management access."""
        self._require_manage_routing(actor)
        catalog = CatalogService(self.db)
        return (
            catalog.list_categories(active=True),
            catalog.list_services(active=True),
        )

    def create_rule(
        self,
        payload: schemas.RoutingRuleCreate,
        actor: ServiceDeskUser,
    ) -> ServiceDeskRoutingRule:
        self._require_manage_routing(actor)
        self._validate_action_assignee(payload.action)
        rule = self.repository.add_rule(
            ServiceDeskRoutingRule(
                name=payload.name.strip(),
                priority=payload.priority,
                is_active=payload.is_active,
                conditions=self._conditions_json(payload.conditions),
                action=payload.action.model_dump(mode="json"),
            )
        )
        self.db.commit()
        return rule

    def update_rule(
        self,
        rule_id: uuid.UUID,
        payload: schemas.RoutingRuleUpdate,
        actor: ServiceDeskUser,
    ) -> ServiceDeskRoutingRule:
        self._require_manage_routing(actor)
        rule = self._require_rule(rule_id)
        data = payload.model_dump(exclude_unset=True)
        conditions = data.get("conditions", rule.conditions)
        action = data.get("action", rule.action)
        definition = schemas.RoutingRuleDefinition.model_validate(
            {"conditions": conditions, "action": action}
        )
        self._validate_action_assignee(definition.action)

        if "name" in data:
            rule.name = payload.name.strip() if payload.name else rule.name
        if "priority" in data:
            rule.priority = payload.priority
        if "is_active" in data:
            rule.is_active = payload.is_active
        rule.conditions = self._conditions_json(definition.conditions)
        rule.action = definition.action.model_dump(mode="json")
        self.db.commit()
        return rule

    def delete_rule(self, rule_id: uuid.UUID, actor: ServiceDeskUser) -> None:
        self._require_manage_routing(actor)
        self.repository.delete_rule(self._require_rule(rule_id))
        self.db.commit()

    def reorder_rules(
        self,
        payload: schemas.RoutingRulesReorder,
        actor: ServiceDeskUser,
    ) -> list[ServiceDeskRoutingRule]:
        self._require_manage_routing(actor)
        rules = self.repository.list_rules()
        current_ids = {rule.id for rule in rules}
        if len(payload.rule_ids) != len(set(payload.rule_ids)) or set(payload.rule_ids) != current_ids:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Передайте полный список правил без повторов",
            )
        by_id = {rule.id: rule for rule in rules}
        for position, rule_id in enumerate(payload.rule_ids):
            by_id[rule_id].priority = position * 100
        self.db.commit()
        return self.repository.list_rules()

    def snapshot_ticket(
        self,
        ticket: ServiceDeskTicket,
        service: ServiceDeskService,
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        now = occurred_at or datetime.now(UTC)
        matched_rules: list[dict[str, Any]] = []
        assignment_rule: dict[str, Any] | None = None

        for rule in self.repository.list_active_rules():
            conditions = self._parse_conditions(rule)
            if not self._matches(ticket, service, conditions):
                continue
            action = schemas.RoutingAction.model_validate(rule.action)
            rule_snapshot = self._rule_snapshot(rule, conditions, action)

            if action.type == "set_priority":
                previous_priority = ticket.priority
                ticket.priority = action.priority
                rule_snapshot["outcome"] = "priority_set"
                rule_snapshot["previous_priority"] = previous_priority.value
                self.ticket_repository.add_history(
                    ServiceDeskTicketHistory(
                        ticket_id=ticket.id,
                        event_type="routing_priority_applied",
                        actor_user_id=None,
                        message="Приоритет заявки установлен правилом маршрутизации",
                        payload={
                            "routing_rule_id": str(rule.id),
                            "routing_rule_name": rule.name,
                            "previous_priority": previous_priority.value,
                            "priority": action.priority.value,
                        },
                    )
                )
            elif assignment_rule is None:
                assignment_rule = rule_snapshot
                rule_snapshot["outcome"] = "assignment_selected"
            else:
                rule_snapshot["outcome"] = "assignment_skipped_by_higher_priority_rule"

            matched_rules.append(rule_snapshot)

        ticket.routing_snapshot = {
            "evaluated_at": now.isoformat(),
            "matched_rules": matched_rules,
            "assignment_rule": assignment_rule,
        }

    def apply_snapshot_assignment(
        self,
        ticket: ServiceDeskTicket,
        *,
        occurred_at: datetime | None = None,
    ) -> bool:
        snapshot = ticket.routing_snapshot or {}
        assignment_rule = snapshot.get("assignment_rule")
        if not assignment_rule:
            return False

        action = schemas.RoutingAction.model_validate(assignment_rule["action"])
        if action.user_id is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "В snapshot отсутствует исполнитель")
        assignee = self.assignee_policy.get_eligible_assignee(action.user_id)
        if not assignee:
            self.ticket_repository.add_history(
                ServiceDeskTicketHistory(
                    ticket_id=ticket.id,
                    event_type="routing_assignment_skipped",
                    actor_user_id=None,
                    message="Исполнитель из правила маршрутизации недоступен",
                    payload={
                        "routing_rule_id": assignment_rule["id"],
                        "routing_rule_name": assignment_rule["name"],
                        "assignee_user_id": str(action.user_id),
                        "assignment_source": "routing_rule",
                    },
                )
            )
            return False

        self.lifecycle.perform_transition(
            ticket,
            ServiceDeskTicketAction.ASSIGN,
            actor=None,
            metadata={
                "assignee_user_id": str(assignee.id),
                "assignment_source": "routing_rule",
                "routing_rule_id": assignment_rule["id"],
                "routing_rule_name": assignment_rule["name"],
            },
            occurred_at=occurred_at,
        )
        return True

    def _validate_action_assignee(self, action: schemas.RoutingAction) -> None:
        if action.type == "assign_user" and action.user_id is not None:
            self.assignee_policy.require_eligible_assignee(action.user_id)

    @staticmethod
    def _conditions_json(
        conditions: list[schemas.RoutingCondition],
    ) -> list[dict[str, Any]]:
        return [condition.model_dump(mode="json") for condition in conditions]

    @staticmethod
    def _rule_snapshot(
        rule: ServiceDeskRoutingRule,
        conditions: list[schemas.RoutingCondition],
        action: schemas.RoutingAction,
    ) -> dict[str, Any]:
        return {
            "id": str(rule.id),
            "name": rule.name,
            "priority": rule.priority,
            "conditions": [condition.model_dump(mode="json") for condition in conditions],
            "action": action.model_dump(mode="json"),
        }

    @staticmethod
    def _parse_conditions(rule: ServiceDeskRoutingRule) -> list[schemas.RoutingCondition]:
        return [schemas.RoutingCondition.model_validate(item) for item in rule.conditions]

    @staticmethod
    def _matches(
        ticket: ServiceDeskTicket,
        service: ServiceDeskService,
        conditions: list[schemas.RoutingCondition],
    ) -> bool:
        for condition in conditions:
            if condition.field == "service_id":
                actual: Any = str(ticket.service_id)
            elif condition.field == "category_id":
                actual = str(service.category_id)
            elif condition.field == "priority":
                actual = ticket.priority.value
            else:
                actual = ticket.field_values.get(condition.field_key or "")

            if actual != condition.value:
                return False
        return True

    def _require_rule(self, rule_id: uuid.UUID) -> ServiceDeskRoutingRule:
        rule = self.repository.get_rule(rule_id)
        if not rule:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Правило маршрутизации не найдено")
        return rule

    @staticmethod
    def _require_manage_routing(actor: ServiceDeskUser) -> None:
        if actor.access_type == ServiceDeskAccessType.SERVICE_DESK_ADMIN:
            return
        if any(item.capability == "service_desk.manage_routing" for item in actor.capabilities):
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для настройки маршрутизации Service Desk")
