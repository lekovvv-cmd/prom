from platform_sdk.error_types import InvalidStateTransition

from app.core.enums import ProjectStatus

_ALLOWED_PROJECT_TRANSITIONS: dict[ProjectStatus, frozenset[ProjectStatus]] = {
    ProjectStatus.DRAFT: frozenset({ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED}),
    ProjectStatus.ACTIVE: frozenset(
        {ProjectStatus.PAUSED, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED}
    ),
    ProjectStatus.PAUSED: frozenset(
        {ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED}
    ),
    ProjectStatus.COMPLETED: frozenset({ProjectStatus.ARCHIVED}),
    ProjectStatus.ARCHIVED: frozenset({ProjectStatus.ACTIVE}),
}


def ensure_project_transition(current: ProjectStatus, target: ProjectStatus) -> None:
    if target == current:
        return
    if target not in _ALLOWED_PROJECT_TRANSITIONS[current]:
        raise InvalidStateTransition(
            f"Переход проекта из {current.value} в {target.value} запрещён"
        )
