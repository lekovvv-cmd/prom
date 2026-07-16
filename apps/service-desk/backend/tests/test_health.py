from app.api.deps import get_db


def test_health_endpoints_are_available(client):
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "alive", "service": "service-desk"}

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert ready.json()["checks"] == {"database": "ok", "storage": "ok"}

    api_health = client.get("/api/health")
    assert api_health.status_code == 200
    assert api_health.json() == {"status": "ok", "service": "service-desk"}


def test_readiness_returns_safe_503_when_database_is_unavailable(client):
    class BrokenDatabase:
        def execute(self, _statement):
            raise RuntimeError("postgresql://user:secret@database/service_desk")

    def broken_db():
        yield BrokenDatabase()

    client.app.dependency_overrides[get_db] = broken_db
    try:
        ready = client.get("/health/ready")
        live = client.get("/health/live")
    finally:
        client.app.dependency_overrides.pop(get_db, None)

    assert ready.status_code == 503
    assert ready.json() == {"status": "not_ready", "service": "service-desk"}
    assert "secret" not in ready.text
    assert live.status_code == 200
