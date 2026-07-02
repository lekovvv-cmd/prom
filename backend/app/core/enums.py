from enum import StrEnum


class UserRole(StrEnum):
    EMPLOYEE = "employee"
    PROJECT_MANAGER = "project_manager"
    ADMIN = "admin"


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectType(StrEnum):
    STRATEGIC = "strategic"


class ProjectPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectResponseStatus(StrEnum):
    NEW = "new"
    VIEWED = "viewed"
    CONTACTED = "contacted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ProjectMemberRole(StrEnum):
    MANAGER = "manager"
    WORKING_GROUP_MEMBER = "working_group_member"
    PARTICIPANT = "participant"


class AttachmentOwnerType(StrEnum):
    PROJECT = "project"
    RESPONSE = "response"
