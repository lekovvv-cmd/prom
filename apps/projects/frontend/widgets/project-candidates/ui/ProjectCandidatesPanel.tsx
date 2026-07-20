import { useEffect, useMemo, useState } from "react";

import { splitCompetencies } from "../../../entities/competency/lib/competencies";
import {
  addAdminProjectMember,
  getAdminProjectCandidates,
} from "../../../entities/project/api/projectApi";
import type {
  ProjectCandidate,
  ProjectCandidateParams,
  ProjectDetails,
} from "../../../entities/project/model/types";
import { Button } from "@prom/ui/Button";
import { Card } from "@prom/ui/Card";
import { EmptyState } from "@prom/ui/EmptyState";
import { Input } from "@prom/ui/Input";
import { Select } from "@prom/ui/Select";
import { Spinner } from "@prom/ui/Spinner";

type Props = {
  project: ProjectDetails;
  onMemberAdded: () => void;
};

export function ProjectCandidatesPanel({ project, onMemberAdded }: Props) {
  const [filters, setFilters] = useState<ProjectCandidateParams>({
    sort: "match_desc",
    limit: 100,
  });
  const [candidates, setCandidates] = useState<ProjectCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [processingUserId, setProcessingUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const competencyOptions = useMemo(
    () =>
      Array.from(
        new Set(
          project.competency_blocks.flatMap((block) => block.competencies),
        ),
      ),
    [project.competency_blocks],
  );

  async function loadCandidates() {
    try {
      setIsLoading(true);
      setError(null);
      const payload = await getAdminProjectCandidates(project.id, filters);
      setCandidates(payload.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить кандидатов",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadCandidates();
  }, [project.id, filters]);

  function updateFilter(nextFilters: Partial<ProjectCandidateParams>) {
    setFilters((current) => ({ ...current, ...nextFilters, offset: 0 }));
  }

  async function addMember(userId: string) {
    try {
      setProcessingUserId(userId);
      setError(null);
      await addAdminProjectMember(project.id, userId);
      await loadCandidates();
      onMemberAdded();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось добавить сотрудника в проект",
      );
    } finally {
      setProcessingUserId(null);
    }
  }

  return (
    <Card className="project-candidates-section">
      <div className="section-heading">
        <div>
          <h3>Подбор сотрудников</h3>
          <p className="muted">
            Поиск по профилям, компетенциям и направлениям работы проекта.
          </p>
        </div>
        <span>{candidates.length} кандидатов</span>
      </div>

      <div className="candidate-filters">
        <Input
          label="Поиск"
          name="candidate_search"
          value={filters.search ?? ""}
          onChange={(event) => updateFilter({ search: event.target.value })}
          placeholder="ФИО, email, должность"
        />
        <Select
          label="Направление"
          name="block_title"
          value={filters.block_title ?? ""}
          isClearable
          clearLabel="Сбросить направление"
          onClear={() => updateFilter({ block_title: "" })}
          onChange={(event) =>
            updateFilter({ block_title: event.target.value })
          }
        >
          <option value="" disabled hidden>
            Все направления
          </option>
          {project.competency_blocks.map((block) => (
            <option key={block.title} value={block.title}>
              {block.title}
            </option>
          ))}
        </Select>
        <Select
          label="Компетенция"
          name="competency"
          value={filters.competency ?? ""}
          isClearable
          clearLabel="Сбросить компетенцию"
          onClear={() => updateFilter({ competency: "" })}
          onChange={(event) => updateFilter({ competency: event.target.value })}
        >
          <option value="" disabled hidden>
            Все компетенции
          </option>
          {competencyOptions.map((competency) => (
            <option key={competency} value={competency}>
              {competency}
            </option>
          ))}
        </Select>
        <Select
          label="Сортировка"
          name="candidate_sort"
          value={filters.sort ?? "match_desc"}
          onChange={(event) =>
            updateFilter({
              sort: event.target.value as ProjectCandidateParams["sort"],
            })
          }
        >
          <option value="match_desc">Лучшие совпадения</option>
          <option value="responses_asc">Без отклика выше</option>
          <option value="name_asc">По имени</option>
        </Select>
      </div>

      {error && <p className="form-error">{error}</p>}
      {isLoading ? (
        <Spinner />
      ) : candidates.length === 0 ? (
        <EmptyState
          title="Кандидаты не найдены"
          text="Измените фильтры или попросите сотрудников заполнить профиль."
        />
      ) : (
        <div className="candidate-list">
          {candidates.map((candidate) => (
            <CandidateRow
              candidate={candidate}
              isProcessing={processingUserId === candidate.id}
              key={candidate.id}
              onAdd={() => void addMember(candidate.id)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function CandidateRow({
  candidate,
  isProcessing,
  onAdd,
}: {
  candidate: ProjectCandidate;
  isProcessing: boolean;
  onAdd: () => void;
}) {
  const competencies = splitCompetencies(candidate.competencies);
  const canAdd = !candidate.is_working_group_member;

  return (
    <article className="candidate-row">
      <div className="candidate-main">
        <strong>{candidate.full_name}</strong>
        <span>{candidate.email}</span>
        <p>
          {[candidate.position, candidate.department]
            .filter(Boolean)
            .join(" - ") || "Профиль без должности"}
        </p>
        {candidate.about && <p className="muted">{candidate.about}</p>}
        <div className="competency-inline">
          {competencies.slice(0, 8).map((competency) => (
            <span
              className={
                candidate.matched_competencies.includes(competency)
                  ? "chip chip-selected"
                  : "chip"
              }
              key={competency}
            >
              {competency}
            </span>
          ))}
        </div>
      </div>
      <div className="candidate-side">
        <span className="candidate-score">{candidate.match_score}</span>
        <small>совпадений</small>
        {candidate.matched_blocks.length > 0 && (
          <span>{candidate.matched_blocks.join(", ")}</span>
        )}
        {candidate.has_response && <span>Уже откликался</span>}
        <Button
          type="button"
          variant={canAdd ? "secondary" : "ghost"}
          disabled={!canAdd || isProcessing}
          onClick={onAdd}
        >
          {candidate.is_working_group_member
            ? "В группе"
            : isProcessing
              ? "Добавляем"
              : "Добавить"}
        </Button>
      </div>
    </article>
  );
}
