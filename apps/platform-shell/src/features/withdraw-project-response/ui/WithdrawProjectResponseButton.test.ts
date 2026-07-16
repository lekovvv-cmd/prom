import { describe, expect, it } from "vitest";

import { canWithdrawResponse } from "./WithdrawProjectResponseButton";

describe("canWithdrawResponse", () => {
  it("allows withdrawal before a final decision", () => {
    expect(canWithdrawResponse("new")).toBe(true);
    expect(canWithdrawResponse("viewed")).toBe(true);
    expect(canWithdrawResponse("contacted")).toBe(true);
  });

  it("blocks withdrawal after a final decision", () => {
    expect(canWithdrawResponse("accepted")).toBe(false);
    expect(canWithdrawResponse("rejected")).toBe(false);
    expect(canWithdrawResponse("cancelled")).toBe(false);
  });
});
