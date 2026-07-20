import { beforeEach, describe, expect, it, vi } from "vitest";

const { accessRequest, projectsRequest } = vi.hoisted(() => ({
  accessRequest: vi.fn(),
  projectsRequest: vi.fn(),
}));

vi.mock("@prom/api-client", () => ({
  accessApiClient: { request: accessRequest },
  apiClient: { request: projectsRequest },
}));

import { getPlatformAuthorization } from "./api";

describe("getPlatformAuthorization", () => {
  beforeEach(() => {
    accessRequest.mockReset();
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
});
