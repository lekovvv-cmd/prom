import { describe, expect, it } from "vitest";

import {
  blocksFromCompetencyString,
  flattenCompetencyBlocks,
  getCoverageForBlock,
  normalizeCompetencyBlocks
} from "./competencyBlocks";

describe("competency block helpers", () => {
  it("keeps old flat competencies compatible", () => {
    expect(blocksFromCompetencyString("SQL, Русский язык")).toEqual([
      {
        title: "Общие компетенции",
        competencies: ["SQL", "Русский язык"]
      }
    ]);
  });

  it("normalizes blocks and flattens competencies for legacy filters", () => {
    const blocks = normalizeCompetencyBlocks([
      { title: " Данные ", competencies: ["SQL", "SQL", ""] },
      { title: "", competencies: ["Русский язык"] }
    ]);

    expect(blocks).toEqual([
      { title: "Данные", competencies: ["SQL"] },
      { title: "Общие компетенции", competencies: ["Русский язык"] }
    ]);
    expect(flattenCompetencyBlocks(blocks)).toBe("SQL, Русский язык");
  });

  it("puts uncovered competencies before covered ones", () => {
    const coverage = getCoverageForBlock(
      { title: "Команда", competencies: ["SQL", "Русский язык"] },
      [
        {
          block_title: "Команда",
          competency: "SQL",
          accepted_count: 2,
          is_covered: true,
          priority: "covered"
        }
      ]
    );

    expect(coverage.map((item) => item.competency)).toEqual(["Русский язык", "SQL"]);
    expect(coverage[0].accepted_count).toBe(0);
    expect(coverage[1].accepted_count).toBe(2);
  });
});
