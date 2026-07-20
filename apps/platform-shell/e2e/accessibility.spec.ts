import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { loginAs } from "./helpers";

async function expectNoSeriousAccessibilityViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const violations = results.violations.filter(
    (violation) =>
      violation.impact === "critical" || violation.impact === "serious",
  );
  expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
}

test("module selector and Projects have no serious automated accessibility violations", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Выберите сервис" }),
  ).toBeVisible();
  await expectNoSeriousAccessibilityViolations(page);

  await loginAs(page, "Сотрудник", "/projects");
  await expect(
    page.getByRole("heading", { name: "Витрина проектов" }),
  ).toBeVisible();
  await expectNoSeriousAccessibilityViolations(page);
});

test("Service Desk catalog has no serious automated accessibility violations", async ({
  page,
}) => {
  await loginAs(page, "Менеджер Service Desk", "/service-desk");
  await expect(
    page.getByRole("heading", { name: "Каталог Service Desk" }),
  ).toBeVisible();
  await expectNoSeriousAccessibilityViolations(page);
});
