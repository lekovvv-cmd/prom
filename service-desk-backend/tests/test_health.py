from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoints_are_available():
    client = TestClient(create_app())

    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "alive", "service": "service-desk"}

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert ready.json()["checks"]["application"] == "ok"

    api_health = client.get("/api/health")
    assert api_health.status_code == 200
    assert api_health.json() == {"status": "ok", "service": "service-desk"}


def test_metrics_endpoint_exposes_prometheus_text():
    client = TestClient(create_app())

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "service_desk_app_info" in response.text
