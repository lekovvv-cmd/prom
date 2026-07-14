import { expect, test } from "@playwright/test";

import { attachScreenshot, loginAs, watchPage } from "./helpers";

test("draft field attachment survives reload, downloads, deletes and is replaced through UI", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const categoryTitle = `Attachment QA category ${suffix}`;
  const serviceTitle = `Attachment QA service ${suffix}`;
  const fieldKey = `qa_file_${suffix}`;
  const fieldLabel = `QA evidence ${suffix}`;
  const ticketTitle = `Attachment QA ticket ${suffix}`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/catalog");
  const categories = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Категории" }) });
  await categories.getByLabel("Новая категория").fill(categoryTitle);
  await categories.getByRole("button", { name: "Создать" }).click();
  const services = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Услуги" }) });
  await services.getByLabel("Новая услуга").fill(serviceTitle);
  await services.getByLabel("Категория").selectOption({ label: categoryTitle });
  await services.getByRole("button", { name: "Создать" }).click();

  await page.goto("/admin/service-desk/templates");
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByRole("button", { name: "Создать новую версию" }).click();
  const editor = page.locator(".template-field-editor");
  await editor.getByLabel("Системное имя поля").fill(fieldKey);
  await editor.getByLabel("Название поля для пользователя").fill(fieldLabel);
  await editor.getByLabel("Тип ответа").selectOption("file");
  await editor.getByText("Это поле обязательно всегда").click();
  await editor.getByRole("button", { name: "Сохранить поле" }).click();
  await page.getByRole("button", { name: "Опубликовать версию" }).click();

  await page.goto("/service-desk");
  await page.getByPlaceholder("Например, доступ к системе").fill(serviceTitle);
  await page.locator(".service-desk-service-card").filter({ hasText: serviceTitle })
    .getByRole("link", { name: "Открыть услугу" }).click();
  await page.getByLabel("Тема заявки").fill(ticketTitle);
  await page.getByLabel("Описание").fill("Проверка файлового поля через production UI.");
  await page.locator(`input#${fieldKey}`).setInputFiles({
    name: "draft-evidence.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("draft attachment evidence")
  });
  await page.getByRole("button", { name: "Сохранить черновик" }).click();
  await expect(page.getByText("Черновик сохранён", { exact: false })).toBeVisible();
  await expect(page.getByRole("list", { name: "Сохранённые файлы" }).getByText("draft-evidence.txt")).toBeVisible();
  await page.getByRole("banner").getByRole("link", { name: "Мои заявки" }).click();
  await page.getByRole("row").filter({ hasText: ticketTitle }).getByRole("link").first().click();
  await expect(page).toHaveURL(/\/service-desk\/tickets\/[^/]+\/edit$/);
  await page.reload();
  const savedFiles = page.getByRole("list", { name: "Сохранённые файлы" });
  await expect(savedFiles.getByText("draft-evidence.txt")).toBeVisible();
  const download = page.waitForEvent("download");
  await savedFiles.getByRole("button", { name: "↓ Скачать" }).click();
  expect((await download).suggestedFilename()).toBe("draft-evidence.txt");
  await savedFiles.getByRole("button", { name: "Удалить" }).click();
  await expect(savedFiles).toHaveCount(0);

  await page.locator(`input#${fieldKey}`).setInputFiles({
    name: "replacement.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("replacement attachment evidence")
  });
  await page.getByRole("button", { name: "Отправить заявку" }).click();
  await expect(page).toHaveURL(/\/service-desk\/tickets\//);
  await expect(page.getByText("replacement.txt")).toBeVisible();
  await attachScreenshot(page, testInfo, "ticket-attachment");
  diagnostics.assertClean();
});
