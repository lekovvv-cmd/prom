import { expect, test } from "@playwright/test";

import { attachScreenshot, loginAs, watchPage } from "./helpers";

test("workbench direct URL exposes operational filters and reloads", async ({
  page,
}, testInfo) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Менеджер Service Desk", "/service-desk/workbench");
  await expect(
    page.getByRole("heading", { name: "Рабочее место Service Desk" }),
  ).toBeVisible();
  await expect(page.getByLabel("Поиск")).toBeVisible();
  await page.getByLabel("Поиск").fill("Browser QA no-match");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Рабочее место Service Desk" }),
  ).toBeVisible();
  await attachScreenshot(page, testInfo, "workbench");
  diagnostics.assertClean();
});
