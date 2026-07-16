import { expect, test } from "@playwright/test";

import { loginAs, watchPage } from "./helpers";

test("my tickets direct URL, filters and reload keep a meaningful state", async ({ page }) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Менеджер Service Desk", "/service-desk/my-tickets");
  await expect(page.getByRole("heading", { name: "Мои заявки" })).toBeVisible();
  await page.getByRole("tablist", { name: "Фильтр заявок" })
    .getByRole("button", { name: "Черновики" }).click();
  await expect(page.getByRole("button", { name: "Черновики" })).toHaveClass(/active/);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Мои заявки" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Создать заявку" })).toBeVisible();
  diagnostics.assertClean();
});
