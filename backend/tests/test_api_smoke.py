def auth_headers(client, email="admin@utmn.ru"):
    request_code = client.post("/api/auth/request-code", json={"email": email})
    assert request_code.status_code == 200

    verify = client.post(
        "/api/auth/verify-code",
        json={"email": email, "code": "000000"},
    )
    assert verify.status_code == 200
    return {"Authorization": f"Bearer {verify.json()['access_token']}"}


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
        "contact_email": "manager@utmn.ru",
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


def test_rejects_non_utmn_email(client):
    response = client.post("/api/auth/request-code", json={"email": "user@example.com"})

    assert response.status_code == 400
    assert "@utmn.ru" in response.json()["detail"]


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
    assert stats.json()["projects_total"] == payload["total"]


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

    manager_headers = auth_headers(client, "manager@utmn.ru")
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
            "email": "analyst@utmn.ru",
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
    analyst_headers = auth_headers(client, "analyst@utmn.ru")
    manager_headers = auth_headers(client, "manager@utmn.ru")
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
            "email": "analyst@utmn.ru",
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


def test_full_mvp_flow(client):
    headers = admin_headers(client)
    me = client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    manager = next(user for user in users.json() if user["email"] == "manager@utmn.ru")
    employee = next(user for user in users.json() if user["email"] == "employee@utmn.ru")
    analyst = next(user for user in users.json() if user["email"] == "analyst@utmn.ru")
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
        "contact_email": "manager@utmn.ru",
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
    download = client.get(text_attachment["download_url"])
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
