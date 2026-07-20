def auth_headers(client, email="admin@utmn.ru"):
    from app.core.database import SessionLocal
    from app.core.security import create_access_token
    from app.modules.users.repository import UserRepository

    with SessionLocal() as db:
        user = UserRepository(db).get_by_email(email)
        assert user is not None
        token = create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}


def admin_headers(client):
    return auth_headers(client, "admin@utmn.ru")


def project_payload(title, status):
    return {
        "title": title,
        "short_description": "Project for response status checks.",
        "description": "Project created by API smoke tests.",
        "goal": "Check response availability by project status.",
        "expected_result": "Response availability is enforced.",
        "project_type": "strategic",
        "priority": "medium",
        "status": status,
        "start_date": None,
        "end_date": None,
        "responsible_user_id": None,
        "contact_email": "project.manager@utmn.ru",
        "required_competencies": "Testing",
        "planned_tasks": "Submit response",
    }


def employee_response_payload(full_name="Pytest Employee"):
    return {
        "full_name": full_name,
        "email": "employee@utmn.ru",
        "comment": "Ready to participate.",
        "competencies": "Testing",
    }


def test_health_checks_database_and_upload_storage(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"database": "ok", "storage": "ok"}
    assert body["database_pool"]["application_name"] == "prom-projects-api"
    assert body["database_pool"]["configured_maximum_connections"] == 10


def test_rejects_non_utmn_email(client):
    assert client.post("/api/auth/request-code", json={"email": "user@example.com"}).status_code == 404
    assert client.post(
        "/api/auth/verify-code",
        json={"email": "user@example.com", "code": "000000"},
    ).status_code == 404


def test_public_projects_hide_archived_seed_project(client):
    response = client.get("/api/projects", params={"limit": 100})

    assert response.status_code == 200
    payload = response.json()
    statuses = {item["status"] for item in payload["items"]}
    titles = {item["title"] for item in payload["items"]}
    assert "archived" not in statuses
    assert "Старая витрина проектных заявок" not in titles

    stats = client.get("/api/admin/stats", headers=admin_headers(client))
    assert stats.status_code == 200
    assert stats.json()["projects_active"] == payload["total"]
    assert stats.json()["projects_total"] == stats.json()["projects_active"] + stats.json()["projects_archived"]


def test_user_can_update_profile_competencies(client):
    headers = auth_headers(client, "employee@utmn.ru")

    updated = client.patch(
        "/api/me/profile",
        json={
            "full_name": "Сотрудник Профиль",
            "department": "ШПИУ",
            "position": "Проектный эксперт",
            "competencies": "SQL, Русский язык",
            "about": "Готов подключаться к проектам с данными и коммуникациями.",
        },
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["competencies"] == "SQL, Русский язык"
    assert updated.json()["about"] == "Готов подключаться к проектам с данными и коммуникациями."

    me = client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["full_name"] == "Сотрудник Профиль"


def test_half_year_reports_are_profile_based_and_admin_controlled(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")
    manager_headers = auth_headers(client, "project.manager@utmn.ru")

    before_open = client.get("/api/reports/current", headers=employee_headers)
    assert before_open.status_code == 200
    assert before_open.json() == {"active_period": None, "report": None}

    blocked_before_open = client.put(
        "/api/reports/current",
        json={"completed_work": "Prepared project materials."},
        headers=employee_headers,
    )
    assert blocked_before_open.status_code == 400

    opened = client.post(
        "/api/admin/reports/periods",
        json={
            "title": "Half-year report 2026-1",
            "starts_on": "2026-01-01",
            "ends_on": "2026-06-30",
        },
        headers=headers,
    )
    assert opened.status_code == 201, opened.text
    period_id = opened.json()["id"]

    current_after_open = client.get("/api/reports/current", headers=employee_headers)
    assert current_after_open.status_code == 200
    assert current_after_open.json()["active_period"]["id"] == period_id
    assert current_after_open.json()["report"] is None

    employee_report = client.put(
        "/api/reports/current",
        json={
            "completed_work": "Prepared materials and helped with communications.",
            "project_results": "Two projects received methodology support.",
            "competencies_used": "Communications, methodology",
            "difficulties": "",
            "next_period_plans": "Support new project practices.",
        },
        headers=employee_headers,
    )
    assert employee_report.status_code == 200, employee_report.text
    assert employee_report.json()["period_id"] == period_id
    assert employee_report.json()["difficulties"] is None

    updated_employee_report = client.put(
        "/api/reports/current",
        json={
            "completed_work": "Updated half-year report.",
            "project_results": None,
            "competencies_used": "Communications",
            "difficulties": None,
            "next_period_plans": None,
        },
        headers=employee_headers,
    )
    assert updated_employee_report.status_code == 200
    assert updated_employee_report.json()["id"] == employee_report.json()["id"]
    assert updated_employee_report.json()["completed_work"] == "Updated half-year report."

    manager_report = client.put(
        "/api/reports/current",
        json={
            "completed_work": "Managed projects and formed working groups.",
            "project_results": "Project teams were assembled.",
        },
        headers=manager_headers,
    )
    assert manager_report.status_code == 200, manager_report.text

    admin_as_user = client.put(
        "/api/reports/current",
        json={"completed_work": "Admin report."},
        headers=headers,
    )
    assert admin_as_user.status_code == 403

    reports = client.get("/api/admin/reports", params={"period_id": period_id}, headers=headers)
    assert reports.status_code == 200
    payload = reports.json()
    assert {item["user"]["email"] for item in payload} == {"employee@utmn.ru", "project.manager@utmn.ru"}
    assert all(item["period"]["id"] == period_id for item in payload)

    periods = client.get("/api/admin/reports/periods", headers=headers)
    assert periods.status_code == 200
    assert periods.json()[0]["id"] == period_id

    closed = client.patch(f"/api/admin/reports/periods/{period_id}/close", headers=headers)
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    after_close_state = client.get("/api/reports/current", headers=manager_headers)
    assert after_close_state.status_code == 200
    assert after_close_state.json() == {"active_period": None, "report": None}


def test_project_search_matches_separate_title_words(client):
    response = client.get("/api/projects", params={"search": "Архив пра", "limit": 100})

    assert response.status_code == 200
    titles = {item["title"] for item in response.json()["items"]}
    assert "Архив проектных практик 2025" in titles

    reversed_response = client.get("/api/projects", params={"search": "пра Архив", "limit": 100})
    assert reversed_response.status_code == 200
    reversed_titles = {item["title"] for item in reversed_response.json()["items"]}
    assert "Архив проектных практик 2025" in reversed_titles


def test_admin_projects_keep_archive_separate(client):
    headers = admin_headers(client)

    current = client.get("/api/admin/projects", params={"limit": 100}, headers=headers)
    assert current.status_code == 200
    current_payload = current.json()
    current_statuses = {item["status"] for item in current_payload["items"]}
    current_titles = {item["title"] for item in current_payload["items"]}
    assert "archived" not in current_statuses
    assert "Старая витрина проектных заявок" not in current_titles

    archive = client.get(
        "/api/admin/projects",
        params={"status": "archived", "limit": 100},
        headers=headers,
    )
    assert archive.status_code == 200
    archive_payload = archive.json()
    archive_statuses = {item["status"] for item in archive_payload["items"]}
    archive_titles = {item["title"] for item in archive_payload["items"]}
    assert archive_payload["total"] >= 1
    assert archive_statuses == {"archived"}
    assert "Старая витрина проектных заявок" in archive_titles

    created = client.post(
        "/api/admin/projects",
        json=project_payload("Pytest project for archive deletion", "active"),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    archived = client.delete(f"/api/admin/projects/{project_id}", headers=headers)
    assert archived.status_code == 200

    archive_after_archive = client.get(
        "/api/admin/projects",
        params={"status": "archived", "search": "Pytest project for archive deletion", "limit": 100},
        headers=headers,
    )
    assert archive_after_archive.status_code == 200
    assert archive_after_archive.json()["total"] == 1

    restored = client.patch(f"/api/admin/projects/{project_id}/restore", headers=headers)
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"

    current_after_restore = client.get(
        "/api/admin/projects",
        params={"search": "Pytest project for archive deletion", "limit": 100},
        headers=headers,
    )
    assert current_after_restore.status_code == 200
    assert current_after_restore.json()["total"] == 1

    archive_after_restore = client.get(
        "/api/admin/projects",
        params={"status": "archived", "search": "Pytest project for archive deletion", "limit": 100},
        headers=headers,
    )
    assert archive_after_restore.status_code == 200
    assert archive_after_restore.json()["total"] == 0

    archived_again = client.delete(f"/api/admin/projects/{project_id}", headers=headers)
    assert archived_again.status_code == 200

    deleted = client.delete(f"/api/admin/projects/{project_id}", headers=headers)
    assert deleted.status_code == 200

    archive_after_delete = client.get(
        "/api/admin/projects",
        params={"status": "archived", "search": "Pytest project for archive deletion", "limit": 100},
        headers=headers,
    )
    assert archive_after_delete.status_code == 200
    assert archive_after_delete.json()["total"] == 0

    from app.core.database import SessionLocal
    from app.modules.projects.models import Project
    from uuid import UUID

    with SessionLocal() as db:
        project = db.get(Project, UUID(project_id))
        assert project is not None
        assert project.deleted_at is not None


def test_competencies_catalog_and_role_access(client):
    catalog = client.get("/api/competencies", params={"search": "SQL"})
    assert catalog.status_code == 200
    assert any(item["name"] == "SQL" for item in catalog.json())

    filtered = client.get("/api/projects", params={"competency": "SQL", "limit": 100})
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1
    assert all("SQL" in item["required_competencies"] for item in filtered.json()["items"])

    multi_filtered = client.get("/api/projects", params={"competency": "SQL, Наставничество", "limit": 100})
    assert multi_filtered.status_code == 200
    multi_competencies = [item["required_competencies"] for item in multi_filtered.json()["items"]]
    assert any("SQL" in competencies for competencies in multi_competencies)
    assert any("Наставничество" in competencies for competencies in multi_competencies)

    manager_headers = auth_headers(client, "project.manager@utmn.ru")
    me = client.get("/api/me", headers=manager_headers)
    assert me.status_code == 200
    assert me.json()["role"] == "project_manager"

    employee_headers = auth_headers(client, "employee@utmn.ru")
    forbidden = client.get("/api/admin/projects", headers=employee_headers)
    assert forbidden.status_code == 403


def test_response_availability_depends_on_project_status(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")

    invalid_contact_payload = project_payload("Pytest invalid contact email project", "active")
    invalid_contact_payload["contact_email"] = "manager@example.com"
    invalid_contact = client.post(
        "/api/admin/projects",
        json=invalid_contact_payload,
        headers=headers,
    )
    assert invalid_contact.status_code == 422
    assert "Разрешены только email" in invalid_contact.text

    paused = client.post(
        "/api/admin/projects",
        json=project_payload("Pytest paused response project", "paused"),
        headers=headers,
    )
    assert paused.status_code == 201, paused.text
    paused_response = client.post(
        f"/api/projects/{paused.json()['id']}/responses",
        json=employee_response_payload("Pytest Paused Response Employee"),
        headers=employee_headers,
    )
    assert paused_response.status_code == 201, paused_response.text

    anonymous_response = client.post(
        f"/api/projects/{paused.json()['id']}/responses",
        json={
            **employee_response_payload("Pytest Anonymous Response Employee"),
            "email": "sd.manager@utmn.ru",
        },
    )
    assert anonymous_response.status_code == 401
    assert "авторизация" in anonymous_response.json()["detail"].lower()

    empty_name_response = client.post(
        f"/api/projects/{paused.json()['id']}/responses",
        json=employee_response_payload(" "),
        headers=employee_headers,
    )
    assert empty_name_response.status_code == 422
    assert "Укажите ФИО" in empty_name_response.text

    invalid_email_payload = {
        **employee_response_payload("Pytest Invalid Email Employee"),
        "email": "employee@example.com",
    }
    invalid_email_response = client.post(
        f"/api/projects/{paused.json()['id']}/responses",
        json=invalid_email_payload,
        headers=employee_headers,
    )
    assert invalid_email_response.status_code == 422
    assert "Разрешены только email" in invalid_email_response.text

    admin_response_payload = {
        **employee_response_payload("Pytest Admin Response Employee"),
        "email": "admin@utmn.ru",
    }
    admin_response = client.post(
        f"/api/projects/{paused.json()['id']}/responses",
        json=admin_response_payload,
        headers=headers,
    )
    assert admin_response.status_code == 403
    assert "Администратор" in admin_response.json()["detail"]

    for status in ("completed", "archived", "draft"):
        created = client.post(
            "/api/admin/projects",
            json=project_payload(f"Pytest {status} response project", status),
            headers=headers,
        )
        assert created.status_code == 201, created.text

        response = client.post(
            f"/api/projects/{created.json()['id']}/responses",
            json=employee_response_payload(f"Pytest {status} Response Employee"),
            headers=employee_headers,
        )
        assert response.status_code == 400
        assert "Отклики доступны только" in response.json()["detail"]


def test_manager_sees_only_own_project_responses(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")
    analyst_headers = auth_headers(client, "sd.manager@utmn.ru")
    manager_headers = auth_headers(client, "project.manager@utmn.ru")
    manager = client.get("/api/me", headers=manager_headers)
    assert manager.status_code == 200
    manager_id = manager.json()["id"]

    owned_project_payload = project_payload("Pytest manager owned response project", "active")
    owned_project_payload["responsible_user_id"] = manager_id
    owned_project = client.post("/api/admin/projects", json=owned_project_payload, headers=headers)
    assert owned_project.status_code == 201, owned_project.text

    other_project = client.post(
        "/api/admin/projects",
        json=project_payload("Pytest hidden response project", "active"),
        headers=headers,
    )
    assert other_project.status_code == 201, other_project.text

    visible_response = client.post(
        f"/api/projects/{owned_project.json()['id']}/responses",
        json=employee_response_payload("Scoped Visible Employee"),
        headers=employee_headers,
    )
    assert visible_response.status_code == 201, visible_response.text

    hidden_response = client.post(
        f"/api/projects/{other_project.json()['id']}/responses",
        json={
            **employee_response_payload("Scoped Hidden Employee"),
            "email": "sd.manager@utmn.ru",
        },
        headers=analyst_headers,
    )
    assert hidden_response.status_code == 201, hidden_response.text

    manager_queue = client.get(
        "/api/admin/responses",
        params={"search": "Scoped", "limit": 100},
        headers=manager_headers,
    )
    assert manager_queue.status_code == 200
    assert manager_queue.json()["total"] == 1
    assert manager_queue.json()["items"][0]["id"] == visible_response.json()["id"]

    manager_projects = client.get(
        "/api/admin/projects",
        params={"limit": 100},
        headers=manager_headers,
    )
    assert manager_projects.status_code == 200
    manager_project_titles = {project["title"] for project in manager_projects.json()["items"]}
    assert "Pytest manager owned response project" in manager_project_titles
    assert "Pytest hidden response project" not in manager_project_titles
    assert "Архив проектных практик 2025" not in manager_project_titles

    visible_project_details = client.get(
        f"/api/admin/projects/{owned_project.json()['id']}",
        headers=manager_headers,
    )
    assert visible_project_details.status_code == 200
    assert visible_project_details.json()["id"] == owned_project.json()["id"]

    hidden_project_details = client.get(
        f"/api/admin/projects/{other_project.json()['id']}",
        headers=manager_headers,
    )
    assert hidden_project_details.status_code == 403

    hidden_project_update = client.patch(
        f"/api/admin/projects/{other_project.json()['id']}",
        json={"short_description": "Manager must not update this project."},
        headers=manager_headers,
    )
    assert hidden_project_update.status_code == 403

    hidden_project_archive = client.delete(
        f"/api/admin/projects/{other_project.json()['id']}",
        headers=manager_headers,
    )
    assert hidden_project_archive.status_code == 403

    hidden_project_queue = client.get(
        f"/api/admin/projects/{other_project.json()['id']}/responses",
        headers=manager_headers,
    )
    assert hidden_project_queue.status_code == 403

    forbidden_patch = client.patch(
        f"/api/admin/responses/{hidden_response.json()['id']}",
        json={"status": "viewed"},
        headers=manager_headers,
    )
    assert forbidden_patch.status_code == 403

    forbidden_delete = client.delete(
        f"/api/admin/responses/{hidden_response.json()['id']}",
        headers=manager_headers,
    )
    assert forbidden_delete.status_code == 403


def test_user_response_list_withdraw_and_admin_delete(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")
    analyst_headers = auth_headers(client, "sd.manager@utmn.ru")

    created = client.post(
        "/api/admin/projects",
        json=project_payload("Pytest response self service project", "active"),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    employee_payload = employee_response_payload("Self Service Employee")
    employee_response = client.post(
        f"/api/projects/{project_id}/responses",
        json=employee_payload,
        headers=employee_headers,
    )
    assert employee_response.status_code == 201, employee_response.text
    employee_response_id = employee_response.json()["id"]

    my_responses = client.get("/api/me/responses", params={"limit": 100}, headers=employee_headers)
    assert my_responses.status_code == 200
    assert any(item["id"] == employee_response_id for item in my_responses.json()["items"])
    assert my_responses.json()["items"][0]["project_title"]

    analyst_responses = client.get("/api/me/responses", params={"limit": 100}, headers=analyst_headers)
    assert analyst_responses.status_code == 200
    assert all(item["id"] != employee_response_id for item in analyst_responses.json()["items"])

    withdrawn = client.delete(f"/api/me/responses/{employee_response_id}", headers=employee_headers)
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "cancelled"

    duplicate_after_withdraw = client.post(
        f"/api/projects/{project_id}/responses",
        json=employee_payload,
        headers=employee_headers,
    )
    assert duplicate_after_withdraw.status_code == 201, duplicate_after_withdraw.text

    analyst_payload = {
        **employee_response_payload("Self Service Analyst"),
        "email": "sd.manager@utmn.ru",
    }
    analyst_response = client.post(
        f"/api/projects/{project_id}/responses",
        json=analyst_payload,
        headers=analyst_headers,
    )
    assert analyst_response.status_code == 201, analyst_response.text
    analyst_response_id = analyst_response.json()["id"]

    deleted = client.delete(f"/api/admin/responses/{analyst_response_id}", headers=headers)
    assert deleted.status_code == 200

    hidden_from_queue = client.get(
        "/api/admin/responses",
        params={"search": "Self Service Analyst", "limit": 100},
        headers=headers,
    )
    assert hidden_from_queue.status_code == 200
    assert hidden_from_queue.json()["total"] == 0

    from app.core.database import SessionLocal
    from app.modules.responses.models import ProjectResponse
    from uuid import UUID

    with SessionLocal() as db:
        response = db.get(ProjectResponse, UUID(analyst_response_id))
        assert response is not None
        assert response.deleted_at is not None


def test_my_projects_include_accepted_responses_and_working_group(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")
    analyst_headers = auth_headers(client, "sd.manager@utmn.ru")

    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    analyst = next(user for user in users.json() if user["email"] == "sd.manager@utmn.ru")

    accepted_project = client.post(
        "/api/admin/projects",
        json=project_payload("Pytest accepted employee project", "active"),
        headers=headers,
    )
    assert accepted_project.status_code == 201, accepted_project.text
    accepted_project_id = accepted_project.json()["id"]

    employee_response = client.post(
        f"/api/projects/{accepted_project_id}/responses",
        json=employee_response_payload("My Projects Employee"),
        headers=employee_headers,
    )
    assert employee_response.status_code == 201, employee_response.text

    before_accept = client.get(
        "/api/me/projects",
        params={"search": "Pytest accepted employee project", "limit": 100},
        headers=employee_headers,
    )
    assert before_accept.status_code == 200
    assert before_accept.json()["total"] == 0

    accepted_response = client.patch(
        f"/api/admin/responses/{employee_response.json()['id']}",
        json={"status": "accepted"},
        headers=headers,
    )
    assert accepted_response.status_code == 200, accepted_response.text

    my_projects = client.get(
        "/api/me/projects",
        params={"search": "Pytest accepted employee project", "limit": 100},
        headers=employee_headers,
    )
    assert my_projects.status_code == 200
    assert my_projects.json()["total"] == 1
    assert my_projects.json()["items"][0]["id"] == accepted_project_id

    my_project_details = client.get(f"/api/me/projects/{accepted_project_id}", headers=employee_headers)
    assert my_project_details.status_code == 200
    assert my_project_details.json()["id"] == accepted_project_id

    forbidden_details = client.get(f"/api/me/projects/{accepted_project_id}", headers=analyst_headers)
    assert forbidden_details.status_code == 403

    group_payload = project_payload("Pytest working group user project", "active")
    group_payload["working_group_member_ids"] = [analyst["id"]]
    group_project = client.post("/api/admin/projects", json=group_payload, headers=headers)
    assert group_project.status_code == 201, group_project.text

    analyst_projects = client.get(
        "/api/me/projects",
        params={"search": "Pytest working group user project", "limit": 100},
        headers=analyst_headers,
    )
    assert analyst_projects.status_code == 200
    assert analyst_projects.json()["total"] == 1
    assert analyst_projects.json()["items"][0]["id"] == group_project.json()["id"]


def test_project_competency_blocks_and_coverage(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")
    analyst_headers = auth_headers(client, "sd.manager@utmn.ru")

    payload = project_payload("Pytest competency coverage project", "active")
    payload["required_competencies"] = None
    payload["competency_blocks"] = [
        {"title": "Данные", "competencies": ["SQL"]},
        {"title": "Коммуникация", "competencies": ["Editorial review"]},
    ]
    project = client.post("/api/admin/projects", json=payload, headers=headers)
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]
    assert project.json()["required_competencies"] == "SQL, Editorial review"

    employee_response = client.post(
        f"/api/projects/{project_id}/responses",
        json={**employee_response_payload("Pytest SQL Employee"), "competencies": "SQL"},
        headers=employee_headers,
    )
    assert employee_response.status_code == 201, employee_response.text
    analyst_response = client.post(
        f"/api/projects/{project_id}/responses",
        json={
            "full_name": "Pytest SQL Analyst",
            "email": "sd.manager@utmn.ru",
            "comment": "Закрываю SQL вторым участником.",
            "competencies": "SQL",
        },
        headers=analyst_headers,
    )
    assert analyst_response.status_code == 201, analyst_response.text

    for response in (employee_response, analyst_response):
        accepted = client.patch(
            f"/api/admin/responses/{response.json()['id']}",
            json={"status": "accepted"},
            headers=headers,
        )
        assert accepted.status_code == 200, accepted.text

    details = client.get(f"/api/admin/projects/{project_id}", headers=headers)
    assert details.status_code == 200, details.text
    coverage = {item["competency"]: item for item in details.json()["competency_coverage"]}
    assert coverage["SQL"]["accepted_count"] == 2
    assert coverage["SQL"]["is_covered"] is True
    assert coverage["SQL"]["priority"] == "covered"
    assert coverage["Editorial review"]["accepted_count"] == 0
    assert coverage["Editorial review"]["is_covered"] is False
    assert coverage["Editorial review"]["priority"] == "open"


def test_project_recommendations_and_profile_competency_response(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")

    profile = client.patch(
        "/api/me/profile",
        json={
            "full_name": "Recommendation Employee",
            "department": "Data lab",
            "position": "Analyst",
            "competencies": "SQL, Data analysis, Visualization",
            "about": "Research and dashboard work.",
        },
        headers=employee_headers,
    )
    assert profile.status_code == 200, profile.text

    payload = project_payload("Pytest recommended data project", "active")
    payload["required_competencies"] = None
    payload["competency_blocks"] = [
        {"title": "Data", "competencies": ["SQL", "Data analysis"]},
        {"title": "Research", "competencies": ["Interview"]},
    ]
    project = client.post("/api/admin/projects", json=payload, headers=headers)
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]

    recommendations = client.get("/api/projects/recommendations", headers=employee_headers)
    assert recommendations.status_code == 200, recommendations.text
    matching = [item for item in recommendations.json() if item["project"]["id"] == project_id]
    assert matching
    assert matching[0]["score"] >= 10
    assert matching[0]["matched_competencies"] == ["SQL", "Data analysis"]
    assert "Совпадают компетенции из профиля" in matching[0]["reasons"]

    response = client.post(
        f"/api/projects/{project_id}/responses",
        json={
            **employee_response_payload("Recommendation Employee"),
            "competencies": "Manual value must be ignored",
        },
        headers=employee_headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["competencies"] == "SQL, Data analysis, Visualization"


def test_project_tasks_workspace_and_result_files(client):
    headers = admin_headers(client)
    employee_headers = auth_headers(client, "employee@utmn.ru")
    analyst_headers = auth_headers(client, "sd.manager@utmn.ru")
    manager_headers = auth_headers(client, "project.manager@utmn.ru")

    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    manager = next(user for user in users.json() if user["email"] == "project.manager@utmn.ru")
    employee = next(user for user in users.json() if user["email"] == "employee@utmn.ru")

    payload = project_payload("Pytest project task workspace", "active")
    payload["responsible_user_id"] = manager["id"]
    payload["working_group_member_ids"] = [employee["id"]]
    project = client.post("/api/admin/projects", json=payload, headers=headers)
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]

    stage = client.post(
        f"/api/admin/projects/{project_id}/stages",
        json={"title": "Discovery", "position": 0, "start_date": "2026-01-01", "end_date": "2026-01-31"},
        headers=manager_headers,
    )
    assert stage.status_code == 201, stage.text

    task = client.post(
        f"/api/admin/projects/{project_id}/tasks",
        json={
            "title": "Prepare research notes",
            "description": "Collect project context and attach result.",
            "stage_id": stage.json()["id"],
            "assignee_user_id": employee["id"],
            "status": "todo",
            "due_date": "2026-01-15",
        },
        headers=manager_headers,
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]
    assert task.json()["is_overdue"] is True
    assert task.json()["assignee"]["id"] == employee["id"]

    manager_stages = client.get(f"/api/admin/projects/{project_id}/stages", headers=manager_headers)
    assert manager_stages.status_code == 200
    assert manager_stages.json()[0]["tasks"][0]["id"] == task_id

    employee_tasks = client.get(f"/api/me/projects/{project_id}/tasks", headers=employee_headers)
    assert employee_tasks.status_code == 200
    assert [item["id"] for item in employee_tasks.json()] == [task_id]

    updated = client.patch(
        f"/api/me/project-tasks/{task_id}",
        json={"status": "in_progress"},
        headers=employee_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "in_progress"

    forbidden_update = client.patch(
        f"/api/me/project-tasks/{task_id}",
        json={"status": "done"},
        headers=analyst_headers,
    )
    assert forbidden_update.status_code == 403

    result_file = client.post(
        f"/api/project-tasks/{task_id}/attachments",
        files={"file": ("result.txt", b"task result", "text/plain")},
        headers=employee_headers,
    )
    assert result_file.status_code == 201, result_file.text
    assert result_file.json()["owner_type"] == "task"

    after_upload = client.get(f"/api/me/projects/{project_id}/tasks", headers=employee_headers)
    assert after_upload.status_code == 200
    assert after_upload.json()[0]["attachments"][0]["file_name"] == "result.txt"

    forbidden_file = client.post(
        f"/api/project-tasks/{task_id}/attachments",
        files={"file": ("other.txt", b"other", "text/plain")},
        headers=analyst_headers,
    )
    assert forbidden_file.status_code == 403


def test_manager_scope_admin_only_and_project_hunting(client):
    headers = admin_headers(client)
    manager_headers = auth_headers(client, "project.manager@utmn.ru")
    employee_headers = auth_headers(client, "employee@utmn.ru")

    users_for_admin = client.get("/api/admin/users", headers=headers)
    assert users_for_admin.status_code == 200
    analyst = next(user for user in users_for_admin.json() if user["email"] == "sd.manager@utmn.ru")

    manager_users = client.get("/api/admin/users", headers=manager_headers)
    assert manager_users.status_code == 403
    manager_stats = client.get("/api/admin/stats", headers=manager_headers)
    assert manager_stats.status_code == 403

    directory = client.get("/api/users/directory", params={"search": "SQL"}, headers=manager_headers)
    assert directory.status_code == 200
    assert any(user["email"] == "sd.manager@utmn.ru" for user in directory.json())

    own_payload = project_payload("Pytest manager hunting project", "active")
    own_payload["required_competencies"] = None
    own_payload["competency_blocks"] = [{"title": "Данные", "competencies": ["SQL"]}]
    own_project = client.post("/api/admin/projects", json=own_payload, headers=manager_headers)
    assert own_project.status_code == 201, own_project.text
    own_project_id = own_project.json()["id"]

    candidates = client.get(
        f"/api/admin/projects/{own_project_id}/candidates",
        params={"competency": "SQL", "sort": "match_desc"},
        headers=manager_headers,
    )
    assert candidates.status_code == 200, candidates.text
    analyst_candidate = next(item for item in candidates.json()["items"] if item["email"] == "sd.manager@utmn.ru")
    assert analyst_candidate["match_score"] >= 1
    assert analyst_candidate["matched_competencies"] == ["SQL"]

    add_member = client.post(
        f"/api/admin/projects/{own_project_id}/members/{analyst['id']}",
        headers=manager_headers,
    )
    assert add_member.status_code == 200, add_member.text
    assert any(
        member["email"] == "sd.manager@utmn.ru" and member["member_role"] == "working_group_member"
        for member in add_member.json()["members"]
    )

    foreign_project = client.post(
        "/api/admin/projects",
        json=project_payload("Pytest admin owned hunting project", "active"),
        headers=headers,
    )
    assert foreign_project.status_code == 201, foreign_project.text
    forbidden_candidates = client.get(
        f"/api/admin/projects/{foreign_project.json()['id']}/candidates",
        headers=manager_headers,
    )
    assert forbidden_candidates.status_code == 403

    employee_directory = client.get("/api/users/directory", headers=employee_headers)
    assert employee_directory.status_code == 200


def test_full_mvp_flow(client):
    headers = admin_headers(client)
    me = client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "platform_admin"

    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    manager = next(user for user in users.json() if user["email"] == "project.manager@utmn.ru")
    employee = next(user for user in users.json() if user["email"] == "employee@utmn.ru")
    analyst = next(user for user in users.json() if user["email"] == "sd.manager@utmn.ru")
    employee_headers = auth_headers(client, "employee@utmn.ru")

    project_payload = {
        "title": "Pytest MVP project",
        "short_description": "Проект для проверки полного сценария.",
        "description": "Создан автоматическим тестом для проверки API MVP.",
        "goal": "Проверить создание проекта, отклик и статистику.",
        "expected_result": "Сценарий выполняется end-to-end.",
        "project_type": "strategic",
        "priority": "high",
        "status": "active",
        "start_date": None,
        "end_date": None,
        "responsible_user_id": manager["id"],
        "working_group_member_ids": [employee["id"], analyst["id"]],
        "contact_email": "project.manager@utmn.ru",
        "required_competencies": "API, тестирование",
        "planned_tasks": "Создать проект, отправить отклик, сменить статус",
    }
    created = client.post("/api/admin/projects", json=project_payload, headers=headers)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    assert created.json()["attachments"] == []
    assert created.json()["responsible"]["id"] == manager["id"]
    assert {member["id"] for member in created.json()["members"]} == {employee["id"], analyst["id"]}

    updated_group = client.patch(
        f"/api/admin/projects/{project_id}",
        json={"working_group_member_ids": [manager["id"]]},
        headers=headers,
    )
    assert updated_group.status_code == 200, updated_group.text
    assert {
        member["id"]
        for member in updated_group.json()["members"]
        if member["member_role"] == "working_group_member"
    } == {manager["id"]}

    project_file = client.post(
        f"/api/admin/projects/{project_id}/attachments",
        headers=headers,
        files={"file": ("brief.txt", b"project brief", "text/plain")},
    )
    assert project_file.status_code == 201, project_file.text
    assert project_file.json()["file_name"] == "brief.txt"

    project_pdf_file = client.post(
        f"/api/admin/projects/{project_id}/attachments",
        headers=headers,
        files={"file": ("brief.pdf", b"%PDF-1.4 project brief", "application/pdf")},
    )
    assert project_pdf_file.status_code == 201, project_pdf_file.text
    assert project_pdf_file.json()["file_name"] == "brief.pdf"

    public_list = client.get("/api/projects", params={"search": "Pytest MVP project"})
    assert public_list.status_code == 200
    assert public_list.json()["total"] == 1
    assert public_list.json()["items"][0]["required_competencies"] == "API, тестирование"
    assert public_list.json()["items"][0]["responsible"]["full_name"] == manager["full_name"]

    filtered_list = client.get("/api/projects", params={"competency": "API"})
    assert filtered_list.status_code == 200
    assert any(item["id"] == project_id for item in filtered_list.json()["items"])

    response_payload = {
        "full_name": "Pytest Employee",
        "email": "employee@utmn.ru",
        "comment": "Хочу участвовать.",
        "competencies": "Коммуникации, тестирование",
    }
    response = client.post(f"/api/projects/{project_id}/responses", json=response_payload, headers=employee_headers)
    assert response.status_code == 201, response.text
    response_id = response.json()["id"]

    duplicate_response = client.post(
        f"/api/projects/{project_id}/responses",
        json=response_payload,
        headers=employee_headers,
    )
    assert duplicate_response.status_code == 409
    assert "уже откликнулись" in duplicate_response.json()["detail"]

    response_file = client.post(
        f"/api/projects/{project_id}/responses/{response_id}/attachments",
        files={"file": ("portfolio.txt", b"portfolio", "text/plain")},
        headers=employee_headers,
    )
    assert response_file.status_code == 201, response_file.text

    response_pdf_file = client.post(
        f"/api/projects/{project_id}/responses/{response_id}/attachments",
        files={"file": ("portfolio.pdf", b"%PDF-1.4 portfolio", "application/pdf")},
        headers=employee_headers,
    )
    assert response_pdf_file.status_code == 201, response_pdf_file.text

    details = client.get(f"/api/projects/{project_id}")
    assert details.status_code == 200
    assert details.json()["responses_count"] == 1
    project_attachment_names = {attachment["file_name"] for attachment in details.json()["attachments"]}
    assert {"brief.txt", "brief.pdf"}.issubset(project_attachment_names)

    text_attachment = next(
        attachment for attachment in details.json()["attachments"] if attachment["file_name"] == "brief.txt"
    )
    download = client.get(text_attachment["download_url"], headers=headers)
    assert download.status_code == 200
    assert download.content == b"project brief"

    responses = client.get(
        "/api/admin/responses",
        params={"search": "Pytest Employee"},
        headers=headers,
    )
    assert responses.status_code == 200
    assert responses.json()["total"] == 1
    response_attachment_names = {
        attachment["file_name"] for attachment in responses.json()["items"][0]["attachments"]
    }
    assert {"portfolio.txt", "portfolio.pdf"}.issubset(response_attachment_names)

    patched = client.patch(
        f"/api/admin/responses/{response_id}",
        json={"status": "contacted"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "contacted"

    stats = client.get("/api/admin/stats", headers=headers)
    assert stats.status_code == 200
    assert any(
        item["project_id"] == project_id and item["responses_count"] == 1
        for item in stats.json()["responses_by_project"]
    )
