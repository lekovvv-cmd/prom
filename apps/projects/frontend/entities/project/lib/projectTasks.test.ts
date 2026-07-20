import { describe, expect, it } from "vitest";

import { splitProjectTasks } from "./projectTasks";

describe("splitProjectTasks", () => {
  it("keeps multiline tasks as separate list items", () => {
    expect(splitProjectTasks("Показать\nПокушать")).toEqual([
      "Показать",
      "Покушать",
    ]);
  });

  it("strips common bullet markers", () => {
    expect(
      splitProjectTasks("- Собрать требования\n* Проверить макеты"),
    ).toEqual(["Собрать требования", "Проверить макеты"]);
  });

  it("ignores empty separators", () => {
    expect(splitProjectTasks("  \n; Подготовить список ;  ")).toEqual([
      "Подготовить список",
    ]);
  });
});
