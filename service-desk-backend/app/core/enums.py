from enum import StrEnum


class ServiceDeskAccessType(StrEnum):
    SERVICE_DESK_MANAGER = "service_desk_manager"
    SERVICE_DESK_ADMIN = "service_desk_admin"


class TemplateVersionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ApprovalMode(StrEnum):
    NONE = "none"
    WORKFLOW = "workflow"


class ApprovalDecisionRule(StrEnum):
    ANY = "any"
    ALL = "all"


class ServiceDeskApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class TemplateFieldType(StrEnum):
    TEXT = "text"
    TEXTAREA = "textarea"
    RICH_TEXT = "rich_text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    FILE = "file"
    USER = "user"


class ServiceDeskTicketStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_REQUESTER = "waiting_requester"
    WAITING_EXTERNAL = "waiting_external"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ServiceDeskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceDeskCommentVisibility(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"


class ServiceDeskAttachmentOwnerType(StrEnum):
    TICKET = "service_desk_ticket"
    COMMENT = "service_desk_comment"
    FIELD_VALUE = "service_desk_field_value"


class ServiceDeskTicketAction(StrEnum):
    SUBMIT = "submit"
    START_APPROVAL = "start_approval"
    SKIP_APPROVAL = "skip_approval"
    COMPLETE_APPROVAL = "complete_approval"
    REJECT_APPROVAL = "reject_approval"
    ASSIGN = "assign"
    REASSIGN = "reassign"
    START = "start"
    REQUEST_CLARIFICATION = "request_clarification"
    REQUESTER_REPLY = "requester_reply"
    WAIT_EXTERNAL = "wait_external"
    RESUME = "resume"
    RESOLVE = "resolve"
    CLOSE = "close"
    CANCEL = "cancel"


SERVICE_DESK_CAPABILITIES: tuple[str, ...] = (
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
