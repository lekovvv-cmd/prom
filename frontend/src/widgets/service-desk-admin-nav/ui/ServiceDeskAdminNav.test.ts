import { describe, expect, it } from "vitest";

import { serviceDeskAdminNavItems } from "./ServiceDeskAdminNav";

describe("ServiceDeskAdminNav", () => {
  it("contains only currently routed admin links", () => {
    const routes = serviceDeskAdminNavItems.map(([, to]) => to);

    expect(routes).toEqual([
      "/admin/service-desk",
      "/admin/service-desk/tickets",
      "/admin/service-desk/catalog",
      "/admin/service-desk/templates",
      "/admin/service-desk/dictionaries",
      "/admin/service-desk/approvals",
      "/admin/service-desk/routing",
      "/admin/service-desk/sla",
      "/admin/service-desk/calendars",
      "/admin/service-desk/access"
    ]);
    expect(routes).not.toContain("/admin/service-desk/notifications");
  });
});
