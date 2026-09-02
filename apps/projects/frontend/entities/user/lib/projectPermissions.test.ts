import { describe, expect, it } from "vitest";

import { canManageProjects } from "./projectPermissions";

describe("Projects permissions", () => {
  it("keeps project-management authorization inside the Projects context", () => {
    expect(
      canManageProjects((permission) => permission === "projects.create"),
    ).toBe(true);
    expect(canManageProjects(() => false)).toBe(false);
  });
});
