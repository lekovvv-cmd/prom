import { afterEach, describe, expect, it, vi } from "vitest";
import { createApiClient } from "./client";
import { renewAccessToken } from "./instances";
import { authTokenStorage } from "./authTokenStorage";

const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const expiredToken = () => {
  const payload = btoa(
    JSON.stringify({ exp: Math.floor(Date.now() / 1000) - 1 }),
  );
  return `header.${payload}.signature`;
};

afterEach(() => {
  vi.unstubAllGlobals();
  authTokenStorage.setToken(null);
});

describe("access token renewal", () => {
  it("uses one browser-session token request for concurrent renewals", async () => {
    const fetchMock = vi.fn(async () => json({ access_token: "fresh" }));
    vi.stubGlobal("fetch", fetchMock);
    expect(
      await Promise.all(Array.from({ length: 5 }, renewAccessToken)),
    ).toEqual(Array.from({ length: 5 }, () => "fresh"));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(authTokenStorage.getToken()).toBe("fresh");
    expect((fetchMock.mock.calls[0][1] as RequestInit).credentials).toBe(
      "include",
    );
  });

  it("clears the token and releases the renewal lock when the browser session expires", async () => {
    authTokenStorage.setToken("stale");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json({ detail: "expired" }, 401))
      .mockResolvedValueOnce(json({ access_token: "recovered" }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(renewAccessToken()).rejects.toMatchObject({
      code: "SESSION_EXPIRED",
    });
    expect(authTokenStorage.getToken()).toBeNull();
    await expect(renewAccessToken()).resolves.toBe("recovered");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("renews once for five concurrent requests and keeps their responses", async () => {
    let token = expiredToken();
    const renew = vi.fn(async () => {
      await Promise.resolve();
      token = "new-token";
      return token;
    });
    const fetchMock = vi.fn(async () => json({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    const client = createApiClient(
      "/api",
      {
        getToken: () => token,
        setToken: (value) => {
          token = value ?? "";
        },
      },
      (() => {
        let flight: Promise<string> | null = null;
        return () =>
          (flight ??= renew().finally(() => {
            flight = null;
          }));
      })(),
    );

    const results = await Promise.all(
      Array.from({ length: 5 }, () => client.request("/tickets")),
    );
    expect(results).toEqual(Array.from({ length: 5 }, () => ({ ok: true })));
    expect(renew).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(5);
    for (const [, init] of fetchMock.mock.calls) {
      expect((init as RequestInit).headers).toBeInstanceOf(Headers);
      expect(
        ((init as RequestInit).headers as Headers).get("Authorization"),
      ).toBe("Bearer new-token");
    }
  });

  it("retries a JSON mutation once after 401 and does not retry 403", async () => {
    let token = "old-token";
    const renew = vi.fn(async () => "new-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json({ detail: "Invalid token" }, 401))
      .mockResolvedValueOnce(json({ created: true }))
      .mockResolvedValueOnce(json({ detail: "Forbidden" }, 403));
    vi.stubGlobal("fetch", fetchMock);
    const client = createApiClient(
      "/api",
      {
        getToken: () => token,
        setToken: (value) => {
          token = value ?? "";
        },
      },
      renew,
    );
    await expect(
      client.request("/tickets", {
        method: "POST",
        body: JSON.stringify({ name: "saved" }),
      }),
    ).resolves.toEqual({ created: true });
    await expect(client.request("/admin")).rejects.toMatchObject({
      status: 403,
    });
    expect(renew).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0][1].body).toBe(
      fetchMock.mock.calls[1][1].body,
    );
  });

  it("renews before a FormData upload and sends the upload exactly once", async () => {
    const renew = vi.fn(async () => "new-token");
    const fetchMock = vi.fn(async () => json({ uploaded: true }));
    vi.stubGlobal("fetch", fetchMock);
    const body = new FormData();
    body.append("file", new Blob(["content"]), "note.txt");
    const client = createApiClient(
      "/api",
      {
        getToken: expiredToken,
        setToken: vi.fn(),
      },
      renew,
    );
    await expect(
      client.request("/attachments", { method: "POST", body }),
    ).resolves.toEqual({ uploaded: true });
    expect(renew).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][1].body).toBe(body);
  });

  it("retries an upload at most once after a bearer 401", async () => {
    const body = new FormData();
    body.append("file", new Blob(["data"]), "file.txt");
    const renew = vi.fn(async () => "new-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json({ detail: "Invalid token" }, 401))
      .mockResolvedValueOnce(json({ detail: "Still invalid" }, 401));
    vi.stubGlobal("fetch", fetchMock);
    const client = createApiClient(
      "/api",
      {
        getToken: () => "old-token",
        setToken: vi.fn(),
      },
      renew,
    );
    await expect(
      client.request("/attachments", { method: "POST", body }),
    ).rejects.toMatchObject({ status: 401 });
    expect(renew).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0][1].body).toBe(body);
    expect(fetchMock.mock.calls[1][1].body).toBe(body);
  });
});
