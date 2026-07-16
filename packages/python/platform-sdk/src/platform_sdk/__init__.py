"""Infrastructure-only building blocks shared by PROM product modules."""

from .auth import CurrentPrincipal, require_permission
from .config import PlatformSettings
from .errors import PlatformError, install_problem_details_handlers

__all__ = [
    "CurrentPrincipal",
    "PlatformError",
    "PlatformSettings",
    "install_problem_details_handlers",
    "require_permission",
]

