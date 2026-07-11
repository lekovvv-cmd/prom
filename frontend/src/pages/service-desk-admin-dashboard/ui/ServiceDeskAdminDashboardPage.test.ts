import { describe, expect, it } from "vitest";

import { buildStatsParams, emptyStatsFilters } from "./ServiceDeskAdminDashboardPage";

describe("ServiceDeskAdminDashboardPage filters", () => {
  it("builds one canonical params object for all stats endpoints", () => {
    const params = buildStatsParams({
      ...emptyStatsFilters,
      dateFrom: "2026-07-10",
      dateTo: "2026-07-11",
      categoryId: "category",
      serviceId: "service",
      assigneeUserId: "assignee",
      priority: "high"
    });

    expect(params.toString()).toBe(
      "date_from=2026-07-10&date_to=2026-07-11&category_id=category&service_id=service&assignee_user_id=assignee&priority=high"
    );
  });
});
