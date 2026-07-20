import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { Select } from "./Select";

describe("Select", () => {
  it("renders a clear button only when a value is selected", () => {
    const emptyHtml = renderToStaticMarkup(
      <Select
        name="project"
        value=""
        onChange={vi.fn()}
        isClearable
        onClear={vi.fn()}
      >
        <option value="" disabled hidden>
          Проект не выбран
        </option>
        <option value="1">Проект</option>
      </Select>,
    );
    const selectedHtml = renderToStaticMarkup(
      <Select
        name="project"
        value="1"
        onChange={vi.fn()}
        isClearable
        onClear={vi.fn()}
      >
        <option value="" disabled hidden>
          Проект не выбран
        </option>
        <option value="1">Проект</option>
      </Select>,
    );

    expect(emptyHtml).not.toContain("select-clear");
    expect(selectedHtml).toContain("select-clear");
    expect(selectedHtml).not.toContain("Все проекты");
  });
});
