import { beforeEach, describe, expect, it, vi } from "vitest";

const { projectsRequest } = vi.hoisted(() => ({ projectsRequest: vi.fn() }));

vi.mock("@prom/api-client", () => ({
  apiClient: { request: projectsRequest },
}));

import {
  getProjectUserDirectory,
  updateProjectProfile,
} from "./projectUserApi";

describe("Projects user API", () => {
  beforeEach(() => projectsRequest.mockReset());

  it("keeps Projects profile and directory requests with Projects contracts", async () => {
    projectsRequest.mockResolvedValue([]);
    await getProjectUserDirectory("Иван");
    expect(projectsRequest).toHaveBeenCalledWith(
      "/users/directory?search=%D0%98%D0%B2%D0%B0%D0%BD",
    );

    projectsRequest.mockResolvedValue({ id: "project-user" });
    await updateProjectProfile({ full_name: "Иван Иванов" });
    expect(projectsRequest).toHaveBeenLastCalledWith("/me/profile", {
      method: "PATCH",
      body: JSON.stringify({ full_name: "Иван Иванов" }),
    });
  });
});
