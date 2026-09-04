"""Exercise interactive Access routes through the public Nginx gateway.

This deliberately uses the standard library HTTP client with no redirect
handler.  It proves the browser-facing versioned routes reach Access instead
of being satisfied by the shell fallback, without treating a TestClient call
as gateway evidence.
"""

from __future__ import annotations

import http.client
import sys
from urllib.parse import quote


HOST = "127.0.0.1"
PORT = 5173


def request(path: str) -> tuple[int, str, str]:
    connection = http.client.HTTPConnection(HOST, PORT, timeout=15)
    try:
        connection.request("GET", path, headers={"Accept": "text/html"})
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        return response.status, response.getheader("Location", ""), body
    finally:
        connection.close()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    status, location, _ = request("/api/access/v1/auth/login?return_url=/projects")
    require(status == 302, f"generic login status: expected 302, got {status}")
    require(
        location == "/auth/mock/login?return_url=/projects",
        f"generic login location: expected mock login redirect, got {location!r}",
    )

    status, location, _ = request("/api/access/v1/auth/mock/login?return_url=/projects")
    require(status == 302, f"versioned mock login status: expected 302, got {status}")
    require(
        location == f"/login?next={quote('/projects', safe='')}",
        f"versioned mock login location: expected shell login redirect, got {location!r}",
    )

    status, location, body = request("/api/access/v1/auth/callback")
    require(status == 400, f"invalid callback must reach Access and return 400, got {status}")
    require(not location, f"invalid callback unexpectedly redirected to {location!r}")
    require("detail" in body.lower(), "invalid callback response is not an Access auth error")
    print("Live gateway Access SSO routing check passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, http.client.HTTPException) as error:
        print(f"Live gateway Access SSO routing check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
