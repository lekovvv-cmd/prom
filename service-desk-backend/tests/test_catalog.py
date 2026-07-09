import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.main import create_app
from app.modules.access import models as access_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def test_admin_can_manage_catalog_and_public_sees_only_active(client: TestClient):
    category = client.post(
        "/admin/categories",
        json={"title": "Сопровождение учебного процесса", "position": 1},
    )
    assert category.status_code == 201, category.text
    category_id = category.json()["id"]

    child = client.post(
        "/admin/categories",
        json={"title": "Практика", "parent_id": category_id, "position": 2},
    )
    assert child.status_code == 201, child.text

    service = client.post(
        "/admin/services",
        json={
            "category_id": category_id,
            "title": "Бронирование аудиторий",
            "short_description": "Заявка на аудиторию для занятия или события.",
            "position": 1,
        },
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]

    public_categories = client.get("/categories")
    assert public_categories.status_code == 200
    assert [item["title"] for item in public_categories.json()] == [
        "Сопровождение учебного процесса",
        "Практика",
    ]

    public_services = client.get("/services", params={"q": "аудитор"})
    assert public_services.status_code == 200
    assert [item["id"] for item in public_services.json()] == [service_id]

    deactivated = client.post(f"/admin/services/{service_id}/deactivate")
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
    assert deactivated.json()["deleted_at"] is not None

    hidden = client.get("/services", params={"q": "аудитор"})
    assert hidden.status_code == 200
    assert hidden.json() == []

    admin_services = client.get("/admin/services", params={"q": "аудитор"})
    assert admin_services.status_code == 200
    assert [item["id"] for item in admin_services.json()] == [service_id]

    restored = client.post(f"/admin/services/{service_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["is_active"] is True
    assert restored.json()["deleted_at"] is None


def test_missing_catalog_entities_return_404(client: TestClient):
    service = client.post(
        "/admin/services",
        json={
            "category_id": "00000000-0000-0000-0000-000000000001",
            "title": "Несуществующая категория",
        },
    )

    assert service.status_code == 404
    assert service.json()["detail"] == "Категория не найдена"
