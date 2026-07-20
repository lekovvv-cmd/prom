import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { filterSearchableOptions, SearchableSelect } from "./SearchableSelect";

const options = [
  { value: "1", label: "Архив проектных практик 2025" },
  { value: "2", label: "Календарь проектных событий" },
  { value: "3", label: "Цифровая карта образовательных инициатив" },
];

describe("filterSearchableOptions", () => {
  it("matches project titles by separate words", () => {
    expect(filterSearchableOptions(options, "архив пра")).toEqual([options[0]]);
    expect(filterSearchableOptions(options, "карта циф")).toEqual([options[2]]);
  });

  it("returns all options for an empty query", () => {
    expect(filterSearchableOptions(options, "")).toEqual(options);
  });
});

describe("SearchableSelect", () => {
  it("renders selected project and clear button", () => {
    const html = renderToStaticMarkup(
      <SearchableSelect
        label="Проект"
        name="project_id"
        value="1"
        options={options}
        onChange={vi.fn()}
      />,
    );

    expect(html).toContain("Архив проектных практик 2025");
    expect(html).toContain("select-clear");
  });
});
