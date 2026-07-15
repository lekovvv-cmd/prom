import { expect, test } from "@playwright/test";

import { attachScreenshot, expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("access management creates, edits capabilities and deactivates by Projects user", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/access");
  await expect(page.getByRole("heading", { name: "Менеджеры и права" })).toBeVisible();
  const accessSearch = page.getByLabel("Поиск", { exact: true });
  const searchResponse = page.waitForResponse((response) =>
    response.request().method() === "GET"
    && response.url().includes("/admin/access/users?")
    && response.url().includes("employee%40utmn.ru")
  );
  await accessSearch.fill("employee@utmn.ru");
  await searchResponse;
  const row = page.getByRole("row").filter({ hasText: "employee@utmn.ru" });
  const status = row.locator("td").nth(3);
  if (await row.count() === 0) {
    await page.getByLabel("Поиск пользователя UTMN").fill("employee@utmn.ru");
    const projectUser = page.getByLabel("Пользователь UTMN");
    await expect(projectUser).toContainText("employee@utmn.ru");
    const projectUserId = await projectUser.locator("option").filter({ hasText: "employee@utmn.ru" })
      .getAttribute("value");
    expect(projectUserId).toBeTruthy();
    await projectUser.selectOption(projectUserId!);
    await page.getByRole("button", { name: "Предоставить доступ" }).click();
    await accessSearch.fill("employee@utmn.ru");
  } else if (await row.getByRole("button", { name: "Активировать" }).count()) {
    await row.getByRole("button", { name: "Активировать" }).click();
    await page.getByRole("dialog", { name: "Активировать доступ" })
      .getByRole("button", { name: "Подтвердить" }).click();
  }
  await expect(status).toHaveText("Активен");
  if (!await row.getByLabel("Работа исполнителем").isChecked()) {
    await row.getByText("Работа исполнителем").click();
  }
  await expect(row.getByLabel("Работа исполнителем")).toBeChecked();
  await row.getByRole("button", { name: "Изменить" }).click();
  const dialog = page.getByRole("dialog", { name: "Изменить профиль доступа" });
  await dialog.getByLabel("Должность").fill("Browser QA temporary profile");
  await dialog.getByRole("button", { name: "Сохранить" }).click();
  await expect(dialog).toBeHidden();
  await expect(status).toHaveText("Активен");
  await row.getByRole("button", { name: "Деактивировать" }).click();
  const confirmation = page.getByRole("dialog", { name: "Деактивировать доступ" });
  await confirmation.getByRole("button", { name: "Подтвердить" }).click();
  await expect(status).toHaveText("Отключен");
  await row.getByRole("button", { name: "Активировать" }).click();
  await page.getByRole("dialog", { name: "Активировать доступ" })
    .getByRole("button", { name: "Подтвердить" }).click();
  await expect(status).toHaveText("Активен");
  await attachScreenshot(page, testInfo, "access-management");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Менеджеры и права" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  diagnostics.assertClean();
});
