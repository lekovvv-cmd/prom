import { expect, test } from "@playwright/test";

import { loginAs, watchPage } from "./helpers";

test("employee session, profile, direct guards and logout stay consistent", async ({ page }) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Сотрудник", "/projects");
  await expect(page.getByRole("heading", { name: "Витрина проектов" })).toBeVisible();
  await page.goto("/profile");
  await expect(page.getByRole("heading", { name: "Профиль" })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Email")).toHaveValue("employee@utmn.ru");
  await page.goto("/admin/projects");
  await expect(page).toHaveURL(/\/projects$/);
  await page.getByRole("button", { name: "Выйти" }).click();
  await page.goto("/profile");
  await expect(page).toHaveURL(/\/login\?next=%2Fprofile$/);
  diagnostics.assertClean();
});

test("project manager keeps project management but no Service Desk access", async ({ page }) => {
  await loginAs(page, "Руководитель проектов", "/admin/projects");
  await expect(page.getByRole("heading", { name: "Управление проектами" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Создать проект" })).toBeVisible();
  await page.goto("/service-desk");
  await expect(page.getByText("У вашей учётной записи нет доступа к Service Desk.")).toBeVisible();
});
