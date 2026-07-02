import type { ProjectFiltersState } from "../model/types";
import { Input } from "../../../shared/ui/Input";
import { Select } from "../../../shared/ui/Select";

type Props = {
  value: ProjectFiltersState;
  onChange: (nextValue: ProjectFiltersState) => void;
  includeArchived?: boolean;
};

export function ProjectFilters({ value, onChange, includeArchived = false }: Props) {
  return (
    <div className="filters">
      <Input
        label="Поиск"
        name="search"
        value={value.search ?? ""}
        onChange={(event) => onChange({ ...value, search: event.target.value })}
        placeholder="Название проекта"
      />
      <Select
        label="Статус"
        name="status"
        value={value.status ?? ""}
        onChange={(event) => onChange({ ...value, status: event.target.value as ProjectFiltersState["status"] })}
      >
        <option value="">Все статусы</option>
        {includeArchived && <option value="draft">Черновик</option>}
        <option value="active">Активен</option>
        <option value="paused">Пауза</option>
        <option value="completed">Завершён</option>
        {includeArchived && <option value="archived">Архив</option>}
      </Select>
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
    </div>
  );
}
