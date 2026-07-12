import { expect, test } from "@playwright/test";

import { attachScreenshot, expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("SLA admin page contract works on desktop and mobile", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/sla");
  await expect(page.getByRole("heading", { name: "SLA Service Desk" })).toBeVisible();
  for (const heading of ["Бизнес-календари", "Политики SLA", "Правила применения SLA", "Эскалации"]) {
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
  }
  await attachScreenshot(page, testInfo, "sla-desktop");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.getByRole("heading", { name: "SLA Service Desk" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await attachScreenshot(page, testInfo, "sla-mobile");
  diagnostics.assertClean();
});
