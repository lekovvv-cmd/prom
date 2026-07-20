from app.modules.competencies.schemas import CompetencyRead

DEFAULT_COMPETENCIES: tuple[CompetencyRead, ...] = (
    CompetencyRead(name="Аналитика данных", group="Данные"),
    CompetencyRead(name="SQL", group="Данные"),
    CompetencyRead(name="Визуализация данных", group="Данные"),
    CompetencyRead(name="Исследования пользователей", group="Исследования"),
    CompetencyRead(name="Интервью", group="Исследования"),
    CompetencyRead(name="Опросы", group="Исследования"),
    CompetencyRead(name="Методология образования", group="Образование"),
    CompetencyRead(name="Наставничество", group="Образование"),
    CompetencyRead(name="Фасилитация", group="Коммуникации"),
    CompetencyRead(name="Коммуникации", group="Коммуникации"),
    CompetencyRead(name="Проектное управление", group="Управление"),
    CompetencyRead(name="Документооборот", group="Управление"),
    CompetencyRead(name="Frontend", group="Разработка"),
    CompetencyRead(name="Backend", group="Разработка"),
    CompetencyRead(name="UX/UI", group="Дизайн"),
)


class CompetencyService:
    def list(self, search: str | None = None) -> list[CompetencyRead]:
        if not search:
            return list(DEFAULT_COMPETENCIES)

        normalized = search.strip().lower()
        return [
            competency
            for competency in DEFAULT_COMPETENCIES
            if normalized in competency.name.lower() or normalized in competency.group.lower()
        ]
