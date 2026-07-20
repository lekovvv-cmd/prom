from platform_sdk.error_types import InvalidStateTransition

from app.core.enums import ProjectResponseStatus

_ALLOWED_RESPONSE_TRANSITIONS: dict[
    ProjectResponseStatus, frozenset[ProjectResponseStatus]
] = {
    ProjectResponseStatus.NEW: frozenset(
        {
            ProjectResponseStatus.VIEWED,
            ProjectResponseStatus.CONTACTED,
            ProjectResponseStatus.ACCEPTED,
            ProjectResponseStatus.REJECTED,
            ProjectResponseStatus.CANCELLED,
        }
    ),
    ProjectResponseStatus.VIEWED: frozenset(
        {
            ProjectResponseStatus.CONTACTED,
            ProjectResponseStatus.ACCEPTED,
            ProjectResponseStatus.REJECTED,
            ProjectResponseStatus.CANCELLED,
        }
    ),
    ProjectResponseStatus.CONTACTED: frozenset(
        {
            ProjectResponseStatus.ACCEPTED,
            ProjectResponseStatus.REJECTED,
            ProjectResponseStatus.CANCELLED,
        }
    ),
    ProjectResponseStatus.ACCEPTED: frozenset(),
    ProjectResponseStatus.REJECTED: frozenset(),
    ProjectResponseStatus.CANCELLED: frozenset(),
}


def ensure_response_transition(
    current: ProjectResponseStatus,
    target: ProjectResponseStatus,
) -> None:
    if target == current:
        return
    if target not in _ALLOWED_RESPONSE_TRANSITIONS[current]:
        raise InvalidStateTransition(
            f"Переход отклика из {current.value} в {target.value} запрещён"
        )
