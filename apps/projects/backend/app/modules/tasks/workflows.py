from platform_sdk.error_types import InvalidStateTransition

from app.core.enums import ProjectTaskStatus

_ALLOWED_TASK_TRANSITIONS: dict[ProjectTaskStatus, frozenset[ProjectTaskStatus]] = {
    ProjectTaskStatus.TODO: frozenset(
        {
            ProjectTaskStatus.IN_PROGRESS,
            ProjectTaskStatus.DONE,
            ProjectTaskStatus.CANCELLED,
        }
    ),
    ProjectTaskStatus.IN_PROGRESS: frozenset(
        {
            ProjectTaskStatus.TODO,
            ProjectTaskStatus.DONE,
            ProjectTaskStatus.CANCELLED,
        }
    ),
    ProjectTaskStatus.DONE: frozenset(),
    ProjectTaskStatus.CANCELLED: frozenset({ProjectTaskStatus.TODO}),
}


def ensure_task_transition(current: ProjectTaskStatus, target: ProjectTaskStatus) -> None:
    if target == current:
        return
    if target not in _ALLOWED_TASK_TRANSITIONS[current]:
        raise InvalidStateTransition(
            f"Переход задачи из {current.value} в {target.value} запрещён"
        )
