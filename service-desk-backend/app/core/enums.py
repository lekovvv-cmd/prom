from enum import StrEnum


class ServiceDeskAccessType(StrEnum):
    MANAGER = "manager"
    SERVICE_DESK_ADMIN = "service_desk_admin"


SERVICE_DESK_CAPABILITIES: tuple[str, ...] = (
    "service_desk.access",
    "service_desk.create_request",
    "service_desk.be_assignee",
    "service_desk.approve",
    "service_desk.assign",
    "service_desk.change_priority",
    "service_desk.view_all_tickets",
    "service_desk.view_reports",
    "service_desk.manage_catalog",
    "service_desk.manage_templates",
    "service_desk.manage_approval_workflows",
    "service_desk.manage_routing",
    "service_desk.manage_sla",
    "service_desk.manage_access",
)


def enum_values(enum_class: type) -> list[str]:
    return [item.value for item in enum_class]
