import { describe, expect, it } from "vitest";

import { ApiError, normalizeApiErrorMessage } from "./client";

describe("generic API errors", () => {
  it("preserves machine-readable problem details", () => {
    const error = new ApiError({
      message: "Conflict",
      status: 409,
      code: "CONFLICT",
      type: "https://errors.example/conflict",
      requestId: "request-1",
      fieldErrors: [
        { field: "name", message: "Already exists", code: "duplicate" },
      ],
      rawDetails: { detail: "Conflict" },
    });
    expect(error).toMatchObject({
      status: 409,
      code: "CONFLICT",
      type: "https://errors.example/conflict",
      requestId: "request-1",
      fieldErrors: [
        { field: "name", message: "Already exists", code: "duplicate" },
      ],
      rawDetails: { detail: "Conflict" },
    });
  });

  it("uses server messages without domain-specific translation", () => {
    expect(
      normalizeApiErrorMessage({
        detail: [
          {
            loc: ["body", "name"],
            msg: "String should have at least 2 characters",
            type: "string_too_short",
          },
        ],
      }),
    ).toBe("String should have at least 2 characters");
  });
});
