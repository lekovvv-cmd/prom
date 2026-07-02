import { useEffect, useMemo, useState } from "react";

import { getCompetencies } from "../api/competencyApi";
import type { Competency } from "../model/types";
import { joinCompetencies, splitCompetencies } from "../lib/competencies";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";

type Props = {
  label: string;
  value: string | null | undefined;
  onChange: (value: string) => void;
};

export function CompetencyPicker({ label, value, onChange }: Props) {
  const selected = useMemo(() => splitCompetencies(value), [value]);
  const [query, setQuery] = useState("");
  const [customValue, setCustomValue] = useState("");
  const [items, setItems] = useState<Competency[]>([]);

  useEffect(() => {
    let ignore = false;
    async function load() {
      const response = await getCompetencies(query);
      if (!ignore) {
        setItems(response);
      }
    }
    void load();
    return () => {
      ignore = true;
    };
  }, [query]);

  function setSelected(next: string[]) {
    onChange(joinCompetencies(next));
  }

  function add(name: string) {
    if (!name.trim() || selected.includes(name.trim())) {
      return;
    }
    setSelected([...selected, name.trim()]);
    setCustomValue("");
  }

  function remove(name: string) {
    setSelected(selected.filter((item) => item !== name));
  }

  return (
    <div className="competency-picker">
      <div className="field-label">{label}</div>
      <div className="competency-selected" aria-label="Выбранные компетенции">
        {selected.length === 0 ? (
          <span className="muted">Компетенции не выбраны</span>
        ) : (
          selected.map((item) => (
            <button key={item} type="button" onClick={() => remove(item)} className="chip chip-selected">
              {item}
              <span aria-hidden="true">×</span>
            </button>
          ))
        )}
      </div>
      <div className="competency-search">
        <Input
          label="Поиск по справочнику"
          name={`${label}-search`}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="SQL, интервью, UX..."
        />
      </div>
      <div className="competency-options">
        {items.map((item) => (
          <button key={item.name} type="button" className="chip" onClick={() => add(item.name)}>
            {item.name}
            <small>{item.group}</small>
          </button>
        ))}
      </div>
      <div className="inline-add">
        <Input
          label="Своя компетенция"
          name={`${label}-custom`}
          value={customValue}
          onChange={(event) => setCustomValue(event.target.value)}
          placeholder="Например: бренд-исследования"
        />
        <Button type="button" variant="secondary" onClick={() => add(customValue)}>
          Добавить
        </Button>
      </div>
    </div>
  );
}
