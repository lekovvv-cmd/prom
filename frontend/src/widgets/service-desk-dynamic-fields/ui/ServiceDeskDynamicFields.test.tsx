import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ServiceDeskDynamicFields } from "./ServiceDeskDynamicFields";

const baseField = {
  template_version_id: "version",
  is_required: true,
  position: 0,
  help_text: null,
  placeholder: null,
  options: null,
  dictionary_code: null,
  validation: null,
  visibility_rules: null,
  required_rules: null,
};

describe("ServiceDeskDynamicFields", () => {
  it("uses database-backed options as type-ahead suggestions for text fields", () => {
    const html = renderToStaticMarkup(
      <ServiceDeskDynamicFields
        fields={[{
          ...baseField,
          id: "discipline",
          key: "discipline",
          label: "Дисциплина",
          field_type: "text",
          dictionary_code: "disciplines",
          effective_options: [{ label: "Информатика", value: "computer_science" }],
        }]}
        values={{ discipline: "Ин" }}
        onChange={() => undefined}
      />,
    );

    expect(html).toContain('list="discipline-options"');
    expect(html).toContain('<datalist id="discipline-options">');
    expect(html).toContain('value="Информатика"');
  });

  it("renders checkbox fields as compact, labeled controls", () => {
    const html = renderToStaticMarkup(
      <ServiceDeskDynamicFields
        fields={[{
          ...baseField,
          id: "requires-substitute",
          key: "requires_substitute_teacher",
          label: "Нужен заменяющий преподаватель",
          field_type: "checkbox",
          is_required: false,
        }]}
        values={{ requires_substitute_teacher: false }}
        onChange={() => undefined}
      />,
    );

    expect(html).toContain("service-desk-checkbox-field");
    expect(html).toContain("service-desk-checkbox-control");
    expect(html).toContain('type="checkbox"');
  });

  it("renders native time and date-time controls for scheduling fields", () => {
    const html = renderToStaticMarkup(
      <ServiceDeskDynamicFields
        fields={[{
          ...baseField,
          id: "new-time",
          key: "new_time",
          label: "Новое время занятия",
          field_type: "time",
        }]}
        values={{ new_time: "10:30" }}
        onChange={() => undefined}
      />,
    );

    expect(html).toContain('type="time"');
    expect(html).toContain('value="10:30"');

    const dateTimeHtml = renderToStaticMarkup(
      <ServiceDeskDynamicFields
        fields={[{
          ...baseField,
          id: "new-datetime",
          key: "new_datetime",
          label: "Новая дата и время занятия",
          field_type: "datetime",
        }]}
        values={{ new_datetime: "2026-07-16T10:30" }}
        onChange={() => undefined}
      />,
    );

    expect(dateTimeHtml).toContain('type="datetime-local"');
    expect(dateTimeHtml).toContain('value="2026-07-16T10:30"');
  });
});
