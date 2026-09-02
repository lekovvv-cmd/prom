import pytest

from platform_sdk.modules import (
    module_access_permission,
    module_python_package,
    module_token_audience,
    validate_module_id,
)


def test_module_convention_preserves_route_id_and_normalizes_permission_namespace() -> None:
    assert validate_module_id("audit-sample-module") == "audit-sample-module"
    assert module_python_package("audit-sample-module") == "audit_sample_module"
    assert module_access_permission("audit-sample-module") == "audit_sample_module.access"
    assert module_token_audience("audit-sample-module") == "audit-sample-module"


@pytest.mark.parametrize("value", ["Audit", "audit_thing", "au", "audit--thing"])
def test_module_convention_rejects_invalid_ids(value: str) -> None:
    with pytest.raises(ValueError):
        validate_module_id(value)
