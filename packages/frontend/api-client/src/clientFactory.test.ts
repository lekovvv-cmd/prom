import { afterEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createApiClient", () => {
  it("creates clients with independent base URLs and shared token storage contract", async () => {
    const tokenStorage = {
      getToken: () => "token-123",
      setToken: vi.fn(),
    };
    const fetchMock = vi.fn(
      async (_input: RequestInfo | URL, _init?: RequestInit) => {
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient("http://service-desk.local", tokenStorage);
    const response = await client.request<{ ok: boolean }>("/health/live");

    expect(response).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://service-desk.local/health/live",
      expect.any(Object),
    );
    const [, init] = fetchMock.mock.calls[0];
    const headers = init?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
  });

  it("returns undefined for successful no-content responses even with a JSON content type", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(null, {
          status: 204,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient("http://service-desk.local", {
      getToken: () => null,
      setToken: vi.fn(),
    });

    await expect(
      client.request<void>("/admin/routing-rules/rule-1", { method: "DELETE" }),
    ).resolves.toBe(undefined);
  });

  it("turns a browser network failure into a clear message for the user", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    const client = createApiClient("http://service-desk.local", {
      getToken: () => null,
      setToken: vi.fn(),
    });

    await expect(client.request("/admin/dictionaries")).rejects.toMatchObject({
      message:
        "Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.",
      status: 0,
    });
  });

  it("parses RFC 9457 problem details served as application/problem+json", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: 409,
            detail: "Категория с таким названием уже существует",
            code: "CONFLICT_DETECTED",
          }),
          {
            status: 409,
            headers: { "Content-Type": "application/problem+json" },
          },
        ),
      ),
    );
    const client = createApiClient("http://service-desk.local", {
      getToken: () => null,
      setToken: vi.fn(),
    });

    await expect(client.request("/admin/categories")).rejects.toMatchObject({
      message: "Категория с таким названием уже существует",
      status: 409,
    });
  });
});
