import { afterEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createApiClient", () => {
  it("creates clients with independent base URLs and shared token storage contract", async () => {
    const tokenStorage = {
      getToken: () => "token-123",
      setToken: vi.fn()
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient("http://service-desk.local", tokenStorage);
    const response = await client.request<{ ok: boolean }>("/health/live");

    expect(response).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith("http://service-desk.local/health/live", expect.any(Object));
    const [, init] = fetchMock.mock.calls[0];
    const headers = init?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
  });
});
