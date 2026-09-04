from access_service.bootstrap.app import app


def test_openapi_contains_session_and_jwks_routes() -> None:
    schema = app.openapi()

    assert "/api/v1/session" in schema["paths"]
    assert "/api/v1/session/probe" in schema["paths"]
    assert "/.well-known/jwks.json" in schema["paths"]


def test_openapi_declares_browser_auth_redirects() -> None:
    schema = app.openapi()

    for path, method in (
        ("/auth/login", "get"),
        ("/auth/callback", "get"),
        ("/auth/logout", "post"),
        ("/auth/mock/login", "get"),
    ):
        responses = schema["paths"][path][method]["responses"]
        assert "302" in responses
        assert "200" not in responses
