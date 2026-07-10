import pytest

from test_access import create_service_desk_user


@pytest.mark.parametrize(
    ("capability", "endpoint_key"),
    [
        ("service_desk.manage_catalog", "catalog"),
        ("service_desk.manage_templates", "templates"),
        ("service_desk.manage_approval_workflows", "approvals"),
        ("service_desk.manage_routing", "routing"),
    ],
)
def test_admin_domains_require_matching_capability_or_service_desk_admin(
    client,
    db_session_factory,
    auth_headers_for_user,
    capability,
    endpoint_key,
):
    category = client.post("/admin/categories", json={"title": "Admin guard category"})
    service = client.post(
        "/admin/services",
        json={"category_id": category.json()["id"], "title": "Admin guard service"},
    )
    version = client.post(f"/admin/services/{service.json()['id']}/versions")
    endpoints = {
        "catalog": "/admin/categories",
        "templates": "/admin/dictionaries",
        "approvals": f"/admin/template-versions/{version.json()['id']}/approval-workflow",
        "routing": "/admin/routing-rules",
    }
    endpoint = endpoints[endpoint_key]

    no_capability = create_service_desk_user(db_session_factory)
    capability_holder = create_service_desk_user(
        db_session_factory,
        capabilities=("service_desk.access", capability),
    )

    assert client.get(endpoint, headers={}).status_code == 401
    assert (
        client.get(endpoint, headers=auth_headers_for_user(str(no_capability.id))).status_code
        == 403
    )
    assert (
        client.get(endpoint, headers=auth_headers_for_user(str(capability_holder.id))).status_code
        == 200
    )
    assert client.get(endpoint, headers=client.admin_headers).status_code == 200

    different_endpoint = next(
        value for key, value in endpoints.items() if key != endpoint_key
    )
    assert (
        client.get(
            different_endpoint,
            headers=auth_headers_for_user(str(capability_holder.id)),
        ).status_code
        == 403
    )
