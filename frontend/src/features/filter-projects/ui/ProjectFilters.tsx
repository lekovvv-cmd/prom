import { useEffect, useState } from "react";

import { getCompetencies } from "../../../entities/competency/api/competencyApi";
import { joinCompetencies, splitCompetencies } from "../../../entities/competency/lib/competencies";
import type { Competency } from "../../../entities/competency/model/types";
import type { ProjectFiltersState } from "../model/types";
import { Input } from "../../../shared/ui/Input";
import { Select } from "../../../shared/ui/Select";

type Props = {
  value: ProjectFiltersState;
  onChange: (nextValue: ProjectFiltersState) => void;
  includeDraft?: boolean;
  includeArchived?: boolean;
  hideStatus?: boolean;
};

export function getVisibleCompetencySuggestions(competencies: Competency[], selected: string[] = []) {
  const selectedSet = new Set(selected);
  return competencies.filter((competency) => !selectedSet.has(competency.name)).slice(0, 8);
}

export function ProjectFilters({ value, onChange, includeDraft = false, includeArchived = false, hideStatus = false }: Props) {
  const [competencySearch, setCompetencySearch] = useState("");
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const selectedCompetencies = splitCompetencies(value.competency);
  const visibleCompetencies = getVisibleCompetencySuggestions(competencies, selectedCompetencies);

  function updateCompetencies(nextCompetencies: string[]) {
    onChange({ ...value, competency: joinCompetencies(nextCompetencies) });
  }

  function addCompetency(name: string) {
    const normalized = name.trim();
    if (!normalized || selectedCompetencies.includes(normalized)) {
      return;
    }
    updateCompetencies([...selectedCompetencies, normalized]);
    setCompetencySearch("");
  }

  function removeCompetency(name: string) {
    updateCompetencies(selectedCompetencies.filter((competency) => competency !== name));
  }

  useEffect(() => {
    let ignore = false;
    async function load() {
      const response = await getCompetencies(competencySearch);
      if (!ignore) {
        setCompetencies(response);
      }
    }
    void load();
    return () => {
      ignore = true;
    };
  }, [competencySearch]);

  return (
    <div className="filters">
      <Input
        label="Поиск"
        name="search"
        value={value.search ?? ""}
        onChange={(event) => onChange({ ...value, search: event.target.value })}
        placeholder="Название проекта"
      />
      {!hideStatus && (
        <Select
          label="Статус"
          name="status"
          value={value.status ?? ""}
          onChange={(event) => onChange({ ...value, status: event.target.value as ProjectFiltersState["status"] })}
        >
          <option value="">Все статусы</option>
          {includeDraft && <option value="draft">Черновик</option>}
          <option value="active">Активен</option>
          <option value="paused">Пауза</option>
          <option value="completed">Завершён</option>
          {includeArchived && <option value="archived">Архив</option>}
        </Select>
      )}
      <Select
        label="Тип"
        name="project_type"
        value={value.project_type ?? ""}
        onChange={(event) =>
          onChange({ ...value, project_type: event.target.value as ProjectFiltersState["project_type"] })
        }
      >
        <option value="">Все типы</option>
        <option value="strategic">Стратегический</option>
      </Select>
      <Select
        label="Сортировка"
        name="sort"
        value={value.sort ?? "created_at_desc"}
        onChange={(event) => onChange({ ...value, sort: event.target.value as ProjectFiltersState["sort"] })}
      >
        <option value="created_at_desc">Новые сначала</option>
        <option value="created_at_asc">Старые сначала</option>
        <option value="priority_desc">Высокий приоритет</option>
        <option value="priority_asc">Низкий приоритет</option>
      </Select>
      <div className="competency-filter-field">
        <Input
          label="Компетенции"
          name="competency"
          value={competencySearch}
          onChange={(event) => setCompetencySearch(event.target.value)}
          placeholder="SQL, интервью..."
        />
        <div className="filter-chips" aria-label="Фильтр по компетенциям">
          {selectedCompetencies.map((competency) => (
            <button
              key={competency}
              type="button"
              className="chip chip-selected"
              onClick={() => removeCompetency(competency)}
            >
              {competency}
              <span aria-hidden="true">×</span>
            </button>
          ))}
          {visibleCompetencies.map((competency) => (
            <button
              key={competency.name}
              type="button"
              className="chip"
              onClick={() => addCompetency(competency.name)}
            >
              {competency.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
