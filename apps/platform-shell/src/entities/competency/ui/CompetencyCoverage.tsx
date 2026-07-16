import type {
  ProjectCompetencyBlock,
  ProjectCompetencyCoverage
} from "../../project/model/types";
import { getCoverageForBlock } from "../lib/competencyBlocks";

type Props = {
  blocks: ProjectCompetencyBlock[];
  coverage?: ProjectCompetencyCoverage[];
};

export function CompetencyCoverage({ blocks, coverage = [] }: Props) {
  if (blocks.length === 0) {
    return <p className="muted">Компетенции не указаны.</p>;
  }

  return (
    <div className="competency-coverage">
      {blocks.map((block) => {
        const items = getCoverageForBlock(block, coverage);
        const coveredCount = items.filter((item) => item.is_covered).length;

        return (
          <section className="competency-coverage-block" key={block.title}>
            <div className="competency-coverage-head">
              <h4>{block.title}</h4>
              <span>
                {coveredCount}/{items.length} закрыто
              </span>
            </div>
            <div className="competency-coverage-list">
              {items.map((item) => (
                <span
                  className={item.is_covered ? "coverage-chip coverage-chip-covered" : "coverage-chip"}
                  key={`${block.title}-${item.competency}`}
                >
                  <strong>{item.competency}</strong>
                  <small>принято: {item.accepted_count}</small>
                </span>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
