import { expect, test, type Page } from "@playwright/test";

async function login(page: Page, role: string, next = "/projects") {
  await page.goto(`/login?next=${encodeURIComponent(next)}`);
  await page.getByRole("button", { name: new RegExp(role), exact: true }).click();
  await page.getByRole("button", { name: /^Войти$/ }).click();
}

for (const role of ["Сотрудник", "Руководитель проектов"]) {
  test(`${role}: Service Desk скрыт и прямой URL закрыт`, async ({ page }) => {
    await login(page, role);
    await expect(page).toHaveURL(/\/projects$/);
    await expect(page.getByLabel("Переключатель модулей").getByText("Service Desk")).toHaveCount(0);
    await page.goto("/service-desk");
    await expect(
      page.getByText("У вашей учётной записи нет доступа к Service Desk.")
    ).toBeVisible();
  });
}

test("Service Desk manager: каталог и заявки доступны без admin sections", async ({ page }) => {
  await login(page, "Менеджер Service Desk", "/service-desk");
  await expect(page.getByRole("heading", { name: "Каталог Service Desk" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Мои заявки" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Администрирование" })).toHaveCount(0);
});

test("Service Desk admin: полный admin navigation доступен", async ({ page }) => {
  await login(page, "Администратор Service Desk", "/admin/service-desk");
  await expect(page.getByRole("heading", { name: "Обзор Service Desk" })).toBeVisible();
  for (const item of [
    "Обзор",
    "Заявки",
    "Каталог",
    "Шаблоны",
    "Справочники",
    "Согласования",
    "Маршрутизация",
    "SLA",
    "Рабочие календари",
    "Менеджеры и права"
  ]) {
    await expect(page.getByRole("link", { name: item, exact: true })).toBeVisible();
  }
});

test("platform admin: Service Desk работает без заранее созданного local profile", async ({ page }) => {
  await login(page, "Администратор платформы", "/service-desk");
  await expect(page.getByRole("heading", { name: "Каталог Service Desk" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Администрирование" })).toBeVisible();
});

test("пустая форма показывает errors и фокусирует первое поле", async ({ page }) => {
  await login(page, "Менеджер Service Desk", "/service-desk");
  await page.getByPlaceholder("Например, доступ к системе").fill("Заказ воды");
  const service = page.locator(".service-desk-service-card").filter({ hasText: "Заказ воды" });
  await service.getByRole("link", { name: "Открыть услугу" }).click();
  await page.getByLabel("Тема заявки").fill("");
  await page.getByLabel("Описание").fill("");
  await page.getByRole("button", { name: "Отправить заявку" }).click();
  await expect(page.getByText("Заполните обязательные поля")).toBeVisible();
  await expect(page.getByText("Укажите тему заявки")).toBeVisible();
  await expect(page.getByLabel("Тема заявки")).toBeFocused();
});
