import { describe, expect, it } from "vitest";

import { canAcceptProjectResponses } from "./responseAvailability";
import type { ProjectStatus } from "../model/types";

describe("canAcceptProjectResponses", () => {
  it("allows responses only for active and paused projects", () => {
    const statuses: ProjectStatus[] = [
      "draft",
      "active",
      "paused",
      "completed",
      "archived",
    ];

    expect(statuses.filter(canAcceptProjectResponses)).toEqual([
      "active",
      "paused",
    ]);
  });
});
