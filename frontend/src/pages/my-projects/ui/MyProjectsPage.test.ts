import { describe, expect, it } from "vitest";

import { getMyProjectsSubtitle } from "./MyProjectsPage";

describe("getMyProjectsSubtitle", () => {
  it("formats participation count", () => {
    expect(getMyProjectsSubtitle(1)).toBe("1 проект, в котором вы участвуете");
    expect(getMyProjectsSubtitle(3)).toBe("3 проекта, в которых вы участвуете");
    expect(getMyProjectsSubtitle(11)).toBe("11 проектов, в которых вы участвуете");
    expect(getMyProjectsSubtitle(21)).toBe("21 проект, в котором вы участвуете");
  });
});
