from access_service.bootstrap.app import app


def test_openapi_contains_session_and_jwks_routes() -> None:
    schema = app.openapi()

    assert "/api/v1/session" in schema["paths"]
    assert "/.well-known/jwks.json" in schema["paths"]
