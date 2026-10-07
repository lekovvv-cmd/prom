"""Verify demo login, browser session, and internal token through Nginx."""

from __future__ import annotations

import http.cookiejar
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5173/api/access/v1"
EMAIL = "employee@utmn.ru"


def request(opener, method: str, path: str, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    response = opener.open(
        urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method),
        timeout=15,
    )
    with response:
        return response.status, json.load(response)


def main() -> int:
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

    status, code = request(opener, "POST", "/auth/mock/code", {"email": EMAIL})
    assert status == 200 and code["dev_code"] == "000000", code
    status, session = request(
        opener, "POST", "/auth/mock/verify", {"email": EMAIL, "code": code["dev_code"]}
    )
    assert status == 200 and session["user"]["email"] == EMAIL, session
    assert any(cookie.name == "prom_session" for cookie in cookies)
    status, token = request(opener, "GET", "/session/token")
    assert status == 200 and token["access_token"], token
    assert token["session"]["user"]["id"] == session["user"]["id"]
    print("Live gateway Access demo login check passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, urllib.error.HTTPError) as error:
        print(f"Live gateway Access demo login check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
