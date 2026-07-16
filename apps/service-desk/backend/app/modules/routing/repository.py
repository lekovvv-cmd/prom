import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.routing.models import ServiceDeskRoutingRule


class RoutingRuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_rules(self) -> list[ServiceDeskRoutingRule]:
        statement = select(ServiceDeskRoutingRule).order_by(
            ServiceDeskRoutingRule.priority.asc(),
            ServiceDeskRoutingRule.created_at.asc(),
        )
        return list(self.db.scalars(statement).all())

    def list_active_rules(self) -> list[ServiceDeskRoutingRule]:
        statement = (
            select(ServiceDeskRoutingRule)
            .where(ServiceDeskRoutingRule.is_active.is_(True))
            .order_by(
                ServiceDeskRoutingRule.priority.asc(),
                ServiceDeskRoutingRule.created_at.asc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def get_rule(self, rule_id: uuid.UUID) -> ServiceDeskRoutingRule | None:
        return self.db.get(ServiceDeskRoutingRule, rule_id)

    def add_rule(self, rule: ServiceDeskRoutingRule) -> ServiceDeskRoutingRule:
        self.db.add(rule)
        self.db.flush()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule: ServiceDeskRoutingRule) -> None:
        self.db.delete(rule)
