import { beforeEach, describe, expect, it, vi } from "vitest";

const { accessRequest, accessSetToken, projectsRequest } = vi.hoisted(() => ({
  accessRequest: vi.fn(),
  accessSetToken: vi.fn(),
  projectsRequest: vi.fn(),
}));

vi.mock("@prom/api-client", () => ({
  accessApiClient: { request: accessRequest, setToken: accessSetToken },
  apiClient: { request: projectsRequest },
}));

import { getAccessSession, getPlatformAuthorization } from "./api";

describe("getPlatformAuthorization", () => {
  beforeEach(() => {
    accessRequest.mockReset();
    accessSetToken.mockReset();
    projectsRequest.mockReset();
  });

  it("uses a path relative to the versioned Access API base URL", async () => {
    accessRequest.mockResolvedValue({
      modules: [{ id: "projects" }],
      permissions: ["projects.access"],
    });

    await expect(getPlatformAuthorization()).resolves.toEqual({
      modules: [{ id: "projects" }],
      permissions: ["projects.access"],
    });
    expect(accessRequest).toHaveBeenCalledWith("/session");
  });

  it("probes an optional cookie session without an anonymous 401", async () => {
    accessRequest.mockResolvedValue({ authenticated: false, token: null });

    await expect(getAccessSession()).rejects.toThrow(
      "No authenticated browser session",
    );
    expect(accessRequest).toHaveBeenCalledWith("/session/probe", {
      auth: false,
    });
    expect(accessSetToken).toHaveBeenCalledWith(null);
  });

  it("keeps the short bearer in memory after a successful probe", async () => {
    accessRequest.mockResolvedValue({
      authenticated: true,
      token: {
        access_token: "short-bearer",
        session: {
          user: {
            id: "user-1",
            email: "user@utmn.ru",
            display_name: "User",
            department: null,
            position: null,
          },
          modules: [{ id: "projects", permissions: ["projects.access"] }],
          permissions: ["projects.access"],
        },
      },
    });

    await expect(getAccessSession()).resolves.toMatchObject({
      user: { id: "user-1", email: "user@utmn.ru" },
      permissions: ["projects.access"],
    });
    expect(accessSetToken).toHaveBeenCalledWith("short-bearer");
  });
});
