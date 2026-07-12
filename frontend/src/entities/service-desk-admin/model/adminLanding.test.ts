import { describe, expect, it } from "vitest";

import { getServiceDeskAdminLanding } from "./adminLanding";

describe("Service Desk admin landing", () => {
  it.each([
    ["service_desk.manage_catalog", "/admin/service-desk/catalog"],
    ["service_desk.manage_templates", "/admin/service-desk/templates"],
    ["service_desk.manage_access", "/admin/service-desk/access"],
    ["service_desk.view_reports", "/admin/service-desk"],
  ])("routes %s to %s", (capability, expected) => {
    expect(getServiceDeskAdminLanding({ access_type: "manager", capabilities: [capability] })).toBe(expected);
  });

  it("routes Service Desk admin to dashboard", () => {
    expect(getServiceDeskAdminLanding({ access_type: "service_desk_admin", capabilities: [] })).toBe("/admin/service-desk");
  });
});
