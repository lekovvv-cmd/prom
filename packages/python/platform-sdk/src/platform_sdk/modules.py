"""Canonical conventions for PROM runtime modules."""

from __future__ import annotations

import re


MODULE_ID_PATTERN = re.compile(r"^(?=.{3,64}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def validate_module_id(module_id: str) -> str:
    """Return a normalized module id or reject a value outside the platform ABI."""

    if not MODULE_ID_PATTERN.fullmatch(module_id):
        raise ValueError("Module id must use lowercase letters, digits, and hyphens")
    return module_id


def module_python_package(module_id: str) -> str:
    return validate_module_id(module_id).replace("-", "_")


def module_access_permission(module_id: str) -> str:
    """The permission required to enter a module's bounded context."""

    return f"{module_python_package(module_id)}.access"


def module_token_audience(module_id: str) -> str:
    """The JWT audience accepted by the module's backend."""

    return validate_module_id(module_id)
