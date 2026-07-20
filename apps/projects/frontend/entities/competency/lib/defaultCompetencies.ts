import type { Competency } from "../model/types";

const DEFAULT_COMPETENCIES: Competency[] = [
  { name: "Аналитика данных", group: "Данные" },
  { name: "SQL", group: "Данные" },
  { name: "Визуализация данных", group: "Данные" },
  { name: "Исследования пользователей", group: "Исследования" },
  { name: "Интервью", group: "Исследования" },
  { name: "Опросы", group: "Исследования" },
  { name: "Методология образования", group: "Образование" },
  { name: "Наставничество", group: "Образование" },
  { name: "Фасилитация", group: "Коммуникации" },
  { name: "Коммуникации", group: "Коммуникации" },
  { name: "Проектное управление", group: "Управление" },
  { name: "Документооборот", group: "Управление" },
  { name: "Frontend", group: "Разработка" },
  { name: "Backend", group: "Разработка" },
  { name: "UX/UI", group: "Дизайн" },
];

export function filterDefaultCompetencies(search?: string) {
  const query = search?.trim().toLowerCase();
  if (!query) {
    return DEFAULT_COMPETENCIES;
  }
  return DEFAULT_COMPETENCIES.filter((item) =>
    `${item.name} ${item.group}`.toLowerCase().includes(query),
  );
}
