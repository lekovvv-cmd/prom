import { describe, expect, it } from "vitest";

import { getAdminProjectListParams } from "./AdminProjectsPage";

describe("getAdminProjectListParams", () => {
  it("keeps archived projects out of the current list request", () => {
    expect(
      getAdminProjectListParams("current", { status: "archived", limit: 100 }),
    ).toEqual({
      status: "",
      limit: 100,
    });
  });

  it("requests only archived projects for the archive view", () => {
    expect(
      getAdminProjectListParams("archive", {
        search: "old",
        status: "active",
        limit: 100,
      }),
    ).toEqual({
      search: "old",
      status: "archived",
      limit: 100,
    });
  });
});
