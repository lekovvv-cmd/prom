import { describe, expect, it } from "vitest";

import {
  buildWorkbenchParams,
  getWorkbenchFiltersFromSearch,
  initialWorkbenchFilters,
  shouldShowInitialWorkbenchSpinner,
  updateWorkbenchFilter,
  updateWorkbenchPage
} from "./workbenchFilters";

describe("workbenchFilters", () => {
  it("updates page without resetting it to the first page", () => {
    expect(updateWorkbenchPage(initialWorkbenchFilters, 2, 3).page).toBe("2");
    expect(updateWorkbenchPage({ ...initialWorkbenchFilters, page: "2" }, 1, 3).page).toBe("1");
  });

  it("clamps page to available boundaries", () => {
    expect(updateWorkbenchPage(initialWorkbenchFilters, 0, 3).page).toBe("1");
    expect(updateWorkbenchPage(initialWorkbenchFilters, 4, 3).page).toBe("3");
  });

  it("resets page when a filter changes", () => {
    const next = updateWorkbenchFilter({ ...initialWorkbenchFilters, page: "2" }, "status", "assigned");
    expect(next).toMatchObject({ status: "assigned", page: "1" });
  });

  it("resets service when category changes", () => {
    const next = updateWorkbenchFilter(
      { ...initialWorkbenchFilters, page: "2", service_id: "service" },
      "category_id",
      "category"
    );
    expect(next).toMatchObject({ category_id: "category", service_id: "", page: "1" });
  });

  it("builds backend pagination and search params", () => {
    const params = buildWorkbenchParams({ ...initialWorkbenchFilters, page: "2", status: "assigned" }, "SD-1");
    expect(params.toString()).toBe("page=2&page_size=25&status=assigned&q=SD-1");
  });

  it("restores a valid quick view from the URL", () => {
    expect(getWorkbenchFiltersFromSearch(new URLSearchParams("quick_view=assigned_to_me"))).toMatchObject({
      page: "1", page_size: "25", quick_view: "assigned_to_me"
    });
    expect(getWorkbenchFiltersFromSearch(new URLSearchParams("quick_view=unknown"))).toEqual(initialWorkbenchFilters);
  });

  it("shows the spinner only for initial loading without existing data", () => {
    expect(shouldShowInitialWorkbenchSpinner(true, false)).toBe(true);
    expect(shouldShowInitialWorkbenchSpinner(true, true)).toBe(false);
    expect(shouldShowInitialWorkbenchSpinner(false, false)).toBe(false);
  });
});
