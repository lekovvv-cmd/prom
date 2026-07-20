import { describe, expect, it } from "vitest";

import { getVisibleCompetencySuggestions } from "./ProjectFilters";
import type { Competency } from "../../../entities/competency/model/types";

const competencies: Competency[] = [
  { name: "SQL", group: "Цифровые навыки" },
  { name: "Аналитика данных", group: "Цифровые навыки" },
  { name: "Интервью", group: "Исследования" },
];

describe("getVisibleCompetencySuggestions", () => {
  it("does not duplicate selected competencies in suggestions", () => {
    expect(
      getVisibleCompetencySuggestions(competencies, ["SQL", "Интервью"]).map(
        (item) => item.name,
      ),
    ).toEqual(["Аналитика данных"]);
  });

  it("limits visible suggestions to eight items", () => {
    const manyCompetencies = Array.from({ length: 12 }, (_, index) => ({
      name: `Competency ${index + 1}`,
      group: "Group",
    }));

    expect(getVisibleCompetencySuggestions(manyCompetencies)).toHaveLength(8);
  });
});
