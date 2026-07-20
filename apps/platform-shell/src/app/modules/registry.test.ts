import { describe, expect, it } from "vitest";

import { getPlatformModuleForPath } from "./registry";

describe("getPlatformModuleForPath", () => {
  it.each([
    ["/projects", "projects"],
    ["/projects/example", "projects"],
    ["/my/projects", "projects"],
    ["/admin/stats", "projects"],
    ["/service-desk", "service-desk"],
    ["/service-desk/my-tickets", "service-desk"],
    ["/admin/service-desk", "service-desk"],
    ["/admin/service-desk/sla", "service-desk"],
  ])("maps %s to the owning module", (pathname, moduleId) => {
    expect(getPlatformModuleForPath(pathname)?.id).toBe(moduleId);
  });

  it("uses segment boundaries and rejects unknown paths", () => {
    expect(getPlatformModuleForPath("/projectsmith")).toBeUndefined();
    expect(getPlatformModuleForPath("/unknown")).toBeUndefined();
  });

  it("prefers the most specific manifest prefix", () => {
    expect(getPlatformModuleForPath("/admin/service-desk/access")?.id).toBe(
      "service-desk",
    );
  });
});
