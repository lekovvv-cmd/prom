from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PlatformError(Exception):
    code: str
    title: str
    status_code: int
    detail: str
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def type(self) -> str:
        return f"https://prom/errors/{self.code.lower().replace('_', '-')}"


class AuthenticationRequired(PlatformError):
    def __init__(self, detail: str = "Authentication is required") -> None:
        super().__init__("AUTHENTICATION_REQUIRED", "Authentication required", 401, detail)


class PermissionDenied(PlatformError):
    def __init__(self, detail: str = "Permission denied") -> None:
        super().__init__("PERMISSION_DENIED", "Permission denied", 403, detail)


class EntityNotFound(PlatformError):
    def __init__(self, detail: str = "Entity not found") -> None:
        super().__init__("ENTITY_NOT_FOUND", "Entity not found", 404, detail)


class InvalidRequest(PlatformError):
    def __init__(self, detail: str = "Invalid request") -> None:
        super().__init__("INVALID_REQUEST", "Invalid request", 400, detail)


class ValidationFailed(PlatformError):
    def __init__(
        self,
        detail: str = "Validation failed",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__("VALIDATION_FAILED", "Validation failed", 422, detail, errors or [])


class ConflictDetected(PlatformError):
    def __init__(self, detail: str = "Conflict detected") -> None:
        super().__init__("CONFLICT_DETECTED", "Conflict detected", 409, detail)


class InvalidStateTransition(PlatformError):
    def __init__(self, detail: str = "Invalid state transition") -> None:
        super().__init__("INVALID_STATE_TRANSITION", "Invalid state transition", 409, detail)


class AssigneeUnavailable(PlatformError):
    def __init__(self, detail: str = "Assignee is unavailable") -> None:
        super().__init__("ASSIGNEE_UNAVAILABLE", "Assignee unavailable", 422, detail)
