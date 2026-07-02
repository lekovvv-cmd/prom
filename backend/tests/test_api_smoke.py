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


def test_competencies_catalog_and_role_access(client):
    catalog = client.get("/api/competencies", params={"search": "SQL"})
    assert catalog.status_code == 200
    assert any(item["name"] == "SQL" for item in catalog.json())

    manager_headers = auth_headers(client, "manager@utmn.ru")
    me = client.get("/api/me", headers=manager_headers)
    assert me.status_code == 200
    assert me.json()["role"] == "project_manager"

    employee_headers = auth_headers(client, "employee@utmn.ru")
    forbidden = client.get("/api/admin/projects", headers=employee_headers)
    assert forbidden.status_code == 403


def test_full_mvp_flow(client):
    headers = admin_headers(client)
    me = client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

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
        "responsible_user_id": None,
        "contact_email": "manager@utmn.ru",
        "required_competencies": "API, тестирование",
        "planned_tasks": "Создать проект, отправить отклик, сменить статус",
    }
    created = client.post("/api/admin/projects", json=project_payload, headers=headers)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    assert created.json()["attachments"] == []

    project_file = client.post(
        f"/api/admin/projects/{project_id}/attachments",
        headers=headers,
        files={"file": ("brief.txt", b"project brief", "text/plain")},
    )
    assert project_file.status_code == 201, project_file.text
    assert project_file.json()["file_name"] == "brief.txt"

    public_list = client.get("/api/projects", params={"search": "Pytest MVP project"})
    assert public_list.status_code == 200
    assert public_list.json()["total"] == 1
    assert public_list.json()["items"][0]["required_competencies"] == "API, тестирование"

    filtered_list = client.get("/api/projects", params={"competency": "API"})
    assert filtered_list.status_code == 200
    assert any(item["id"] == project_id for item in filtered_list.json()["items"])

    response_payload = {
        "full_name": "Pytest Employee",
        "email": "employee@utmn.ru",
        "comment": "Хочу участвовать.",
        "competencies": "Коммуникации, тестирование",
    }
    response = client.post(f"/api/projects/{project_id}/responses", json=response_payload)
    assert response.status_code == 201, response.text
    response_id = response.json()["id"]

    response_file = client.post(
        f"/api/projects/{project_id}/responses/{response_id}/attachments",
        files={"file": ("portfolio.txt", b"portfolio", "text/plain")},
    )
    assert response_file.status_code == 201, response_file.text

    details = client.get(f"/api/projects/{project_id}")
    assert details.status_code == 200
    assert details.json()["responses_count"] == 1
    assert details.json()["attachments"][0]["file_name"] == "brief.txt"

    download = client.get(details.json()["attachments"][0]["download_url"])
    assert download.status_code == 200
    assert download.content == b"project brief"

    responses = client.get(
        "/api/admin/responses",
        params={"search": "Pytest Employee"},
        headers=headers,
    )
    assert responses.status_code == 200
    assert responses.json()["total"] == 1
    assert responses.json()["items"][0]["attachments"][0]["file_name"] == "portfolio.txt"

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
