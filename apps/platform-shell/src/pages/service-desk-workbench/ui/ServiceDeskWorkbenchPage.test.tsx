import { describe, expect, it } from "vitest";
import { workbenchStatusOptions } from "./ServiceDeskWorkbenchPage";

describe("ServiceDeskWorkbenchPage status filter", () => {
  it("contains relevant non-draft backend statuses", () => {
    const values = workbenchStatusOptions.map(([value]) => value);

    expect(values).toContain("submitted");
    expect(values).toContain("rejected");
    expect(values).toContain("cancelled");
    expect(values).toContain("pending_approval");
    expect(values).toContain("assigned");
    expect(values).toContain("closed");
    expect(values).not.toContain("draft");
  });
});
