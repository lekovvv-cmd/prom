import { describe, expect, it } from "vitest";

import {
  canShowServiceDeskAdministration,
  getServiceDeskAdminLanding,
} from "./adminLanding";

describe("Service Desk admin landing", () => {
  it.each([
    ["service_desk.manage_catalog", "/admin/service-desk/catalog"],
    ["service_desk.manage_templates", "/admin/service-desk/templates"],
    ["service_desk.manage_access", "/admin/service-desk/access"],
    ["service_desk.view_reports", "/admin/service-desk"],
  ])("routes %s to %s", (capability, expected) => {
    expect(
      getServiceDeskAdminLanding({
        access_type: "service_desk_manager",
        capabilities: [capability],
      }),
    ).toBe(expected);
  });

  it("routes Service Desk admin to dashboard", () => {
    expect(
      getServiceDeskAdminLanding({
        access_type: "service_desk_admin",
        capabilities: [],
      }),
    ).toBe("/admin/service-desk");
  });

  it("keeps the administration entry hidden for a view-only manager", () => {
    expect(
      canShowServiceDeskAdministration({
        access_type: "service_desk_manager",
        capabilities: [
          "service_desk.view_all_tickets",
          "service_desk.view_reports",
        ],
      }),
    ).toBe(false);
  });

  it.each([
    {
      access_type: "service_desk_admin" as const,
      capabilities: [] as string[],
    },
    {
      access_type: "service_desk_manager" as const,
      capabilities: ["service_desk.manage_catalog"],
    },
  ])(
    "shows the administration entry for $access_type with admin access",
    (user) => {
      expect(canShowServiceDeskAdministration(user)).toBe(true);
    },
  );
});
