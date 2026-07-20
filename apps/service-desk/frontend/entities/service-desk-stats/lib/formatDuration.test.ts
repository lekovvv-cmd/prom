import { describe, expect, it } from "vitest";
import { formatDuration } from "./formatDuration";
describe("formatDuration", () => {
  it("formats duration and missing samples", () => {
    expect(formatDuration(null)).toBe("Нет данных");
    expect(formatDuration(8100)).toBe("2 ч 15 мин");
    expect(formatDuration(97200)).toBe("1 д 3 ч");
  });
});
