import { describe, expect, it } from "vitest";

import { isUtmnEmail, normalizeEmail } from "./email";

describe("email helpers", () => {
  it("normalizes email before submit", () => {
    expect(normalizeEmail(" Employee@UTMN.RU ")).toBe("employee@utmn.ru");
  });

  it("accepts only valid utmn email shape", () => {
    expect(isUtmnEmail("employee@utmn.ru")).toBe(true);
    expect(isUtmnEmail("employee@example.com")).toBe(false);
    expect(isUtmnEmail(" @utmn.ru")).toBe(false);
    expect(isUtmnEmail("employee@@utmn.ru")).toBe(false);
  });
});
