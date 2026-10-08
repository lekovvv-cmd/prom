from access_service.bootstrap.app import app


def test_openapi_contains_session_and_jwks_routes() -> None:
    schema = app.openapi()

    assert "/api/v1/session" in schema["paths"]
    assert "/api/v1/session/probe" in schema["paths"]
    assert "/.well-known/jwks.json" in schema["paths"]


def test_openapi_declares_demo_session_routes() -> None:
    schema = app.openapi()

    assert "/api/v1/auth/mock/code" in schema["paths"]
    assert "/api/v1/auth/mock/verify" in schema["paths"]
    assert "/api/v1/session/token" in schema["paths"]
    assert "/auth/callback" not in schema["paths"]
