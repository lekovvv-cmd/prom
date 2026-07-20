import type {
  ProjectCompetencyBlock,
  ProjectCompetencyCoverage,
} from "../../project/model/types";
import { joinCompetencies, splitCompetencies } from "./competencies";

const DEFAULT_COMPETENCY_BLOCK_TITLE = "Общие компетенции";

export function createEmptyCompetencyBlock(): ProjectCompetencyBlock {
  return {
    title: "Новое направление",
    competencies: [],
  };
}

export function blocksFromCompetencyString(
  value: string | null | undefined,
): ProjectCompetencyBlock[] {
  const competencies = splitCompetencies(value);
  if (competencies.length === 0) {
    return [];
  }

  return [
    {
      title: DEFAULT_COMPETENCY_BLOCK_TITLE,
      competencies,
    },
  ];
}

export function normalizeCompetencyBlocks(
  blocks: ProjectCompetencyBlock[] | null | undefined,
  fallbackCompetencies?: string | null,
): ProjectCompetencyBlock[] {
  const normalized = (blocks ?? [])
    .map((block) => ({
      title: block.title.trim() || DEFAULT_COMPETENCY_BLOCK_TITLE,
      competencies: splitCompetencies(
        joinCompetencies(block.competencies ?? []),
      ),
    }))
    .filter((block) => block.competencies.length > 0);

  return normalized.length > 0
    ? normalized
    : blocksFromCompetencyString(fallbackCompetencies);
}

export function flattenCompetencyBlocks(
  blocks: ProjectCompetencyBlock[],
): string {
  return joinCompetencies(blocks.flatMap((block) => block.competencies));
}

export function getCoverageForBlock(
  block: ProjectCompetencyBlock,
  coverage: ProjectCompetencyCoverage[] = [],
): ProjectCompetencyCoverage[] {
  const coverageByName = new Map(
    coverage.map((item) => [item.competency.toLocaleLowerCase("ru-RU"), item]),
  );

  return block.competencies
    .map((competency) => {
      const item = coverageByName.get(competency.toLocaleLowerCase("ru-RU"));
      return (
        item ?? {
          block_title: block.title,
          competency,
          accepted_count: 0,
          is_covered: false,
          priority: "open" as const,
        }
      );
    })
    .sort((left, right) => {
      if (left.is_covered !== right.is_covered) {
        return left.is_covered ? 1 : -1;
      }
      return left.competency.localeCompare(right.competency, "ru-RU");
    });
}
