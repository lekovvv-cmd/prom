from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from platform_sdk.observability import (
    ServiceMetrics,
    install_metrics_endpoint,
    install_request_context,
)


def test_prometheus_endpoint_exposes_low_cardinality_http_metrics() -> None:
    app = FastAPI()
    metrics = ServiceMetrics(service="test-service", module="test-module")
    install_request_context(app, metrics=metrics)
    install_metrics_endpoint(app, metrics)

    @app.get("/items/{item_id}")
    def item(item_id: str) -> dict[str, str]:
        return {"id": item_id}

    with TestClient(app) as client:
        assert client.get("/items/123").status_code == 200
        body = client.get("/metrics").text

    assert "prom_http_requests_total" in body
    assert 'route="/items/{item_id}"' in body
    assert 'route="/items/123"' not in body
    assert 'service="test-service"' in body
