import { Plus, Trash2 } from "lucide-react";

import type { ProjectCompetencyBlock } from "../../project/model/types";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { createEmptyCompetencyBlock } from "../lib/competencyBlocks";
import { joinCompetencies, splitCompetencies } from "../lib/competencies";
import { CompetencyPicker } from "./CompetencyPicker";

type Props = {
  label: string;
  value: ProjectCompetencyBlock[];
  onChange: (value: ProjectCompetencyBlock[]) => void;
};

export function CompetencyBlocksEditor({ label, value, onChange }: Props) {
  const blocks = value.length > 0 ? value : [createEmptyCompetencyBlock()];

  function updateBlock(index: number, block: ProjectCompetencyBlock) {
    onChange(blocks.map((item, currentIndex) => (currentIndex === index ? block : item)));
  }

  function addBlock() {
    onChange([...blocks, createEmptyCompetencyBlock()]);
  }

  function removeBlock(index: number) {
    const nextBlocks = blocks.filter((_, currentIndex) => currentIndex !== index);
    onChange(nextBlocks.length > 0 ? nextBlocks : [createEmptyCompetencyBlock()]);
  }

  return (
    <div className="competency-blocks-editor">
      <div className="section-heading compact">
        <div>
          <span className="field-label">{label}</span>
          <p className="muted">Направление работы объединяет близкие задачи и компетенции.</p>
        </div>
        <Button type="button" variant="secondary" onClick={addBlock}>
          <Plus size={15} />
          Добавить направление
        </Button>
      </div>
      <div className="competency-blocks-list">
        {blocks.map((block, index) => (
          <section className="competency-block-editor" key={`${block.title}-${index}`}>
            <div className="competency-block-editor-head">
              <Input
                label="Название направления"
                name={`competency-block-${index}`}
                value={block.title}
                onChange={(event) => updateBlock(index, { ...block, title: event.target.value })}
                placeholder="Например: Коммуникация"
              />
              <Button type="button" variant="danger" onClick={() => removeBlock(index)} aria-label="Удалить направление">
                <Trash2 size={15} />
              </Button>
            </div>
            <CompetencyPicker
              label="Компетенции направления"
              value={joinCompetencies(block.competencies)}
              onChange={(competencies) =>
                updateBlock(index, {
                  ...block,
                  competencies: splitCompetencies(competencies)
                })
              }
            />
          </section>
        ))}
      </div>
    </div>
  );
}
