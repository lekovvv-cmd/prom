import { expect, test, type Locator, type Page } from "@playwright/test";

function uniqueProjectTitle() {
  return `E2E проект ${Date.now()}`;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function loginAs(page: Page, roleLabel: "Администратор платформы" | "Сотрудник") {
  await page.goto("/login");
  await page.getByRole("button", { name: new RegExp(roleLabel), exact: true }).click();
  await page.getByRole("button", { name: /^Войти$/ }).click();
  await expect(page.getByRole("link", { name: "Витрина" })).toBeVisible();
}

async function logout(page: Page) {
  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page.getByRole("banner").getByRole("link", { name: "Войти" })).toBeVisible();
}

async function addCustomCompetency(scope: Locator, value: string) {
  await scope.getByLabel("Своя компетенция").fill(value);
  await scope.getByRole("button", { name: "Добавить" }).click();
  await expect(scope.getByRole("button", { name: new RegExp(escapeRegExp(value)) })).toBeVisible();
}

test("MVP flow: admin creates project, employee responds, admin updates status and stats", async ({ page }) => {
  const projectTitle = uniqueProjectTitle();
  const responseName = `E2E Сотрудник ${Date.now()}`;

  await loginAs(page, "Администратор платформы");

  await page.getByRole("link", { name: /Управление/ }).click();
  await expect(page.getByRole("heading", { name: "Управление проектами" })).toBeVisible();

  await page.getByRole("button", { name: "Создать проект" }).click();
  const dialog = page.getByRole("dialog", { name: "Создать проект" });
  await expect(dialog).toBeVisible();

  await dialog.getByLabel("Название", { exact: true }).fill(projectTitle);
  await dialog.getByLabel("Краткое описание").fill("Проект создан браузерным автотестом.");
  await dialog.getByLabel("Полное описание").fill("Проверяет главный сценарий MVP через пользовательский интерфейс.");
  await dialog.getByLabel("Цель").fill("Проверить создание проекта, отклик, статус и статистику.");
  await dialog.getByLabel("Ожидаемый результат").fill("Проект отображается в витрине и принимает отклик.");
  await expect(dialog.getByLabel("Ответственный")).toContainText("Руководитель проекта - Руководитель");
  await dialog.getByLabel("Ответственный").selectOption({ label: "Руководитель проекта - Руководитель" });
  await dialog.getByLabel(/employee@utmn\.ru/).check();
  await dialog.getByLabel("Название направления").fill("Тестирование");
  await addCustomCompetency(dialog.locator(".competency-block-editor").first(), "E2E компетенция");
  await dialog.getByLabel("Планируемые задачи").fill("Показать\nПокушать");
  await dialog.locator('input[type="file"]').setInputFiles([
    {
      name: "project-brief.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("project brief")
    },
    {
      name: "project-plan.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# plan")
    }
  ]);
  await expect(dialog.getByText("project-brief.txt")).toBeVisible();
  await expect(dialog.getByText("project-plan.md")).toBeVisible();
  await dialog.getByRole("button", { name: "Создать проект" }).click();
  await expect(dialog).toBeHidden();
  await expect(page.getByText(projectTitle)).toBeVisible();

  await page.getByRole("link", { name: "Витрина" }).click();
  await page.getByLabel("Поиск").fill(projectTitle);
  const projectLink = page.getByRole("link", { name: new RegExp(escapeRegExp(projectTitle)) });
  await expect(projectLink).toBeVisible();
  await projectLink.click();
  await expect(page.getByRole("heading", { level: 1, name: projectTitle })).toBeVisible();
  await expect(page.locator(".task-list li").filter({ hasText: "Показать" })).toBeVisible();
  await expect(page.locator(".task-list li").filter({ hasText: "Покушать" })).toBeVisible();
  await expect(page.getByText("project-brief.txt")).toBeVisible();
  await expect(page.getByText("Сотрудник ШПИУ")).toBeVisible();
  await expect(page.getByText("Отклики недоступны")).toBeVisible();

  await logout(page);
  await loginAs(page, "Сотрудник");

  await page.getByLabel("Поиск").fill(projectTitle);
  await page.getByRole("link", { name: new RegExp(escapeRegExp(projectTitle)) }).click();
  await expect(page.getByRole("heading", { name: "Откликнуться на проект" })).toBeVisible();

  await page.getByLabel("ФИО").fill(responseName);
  await page.getByLabel("Email").fill("employee@utmn.ru");
  await page.getByLabel("Комментарий").fill("Готов участвовать в проекте.");
  await page.locator('input[type="file"]').setInputFiles({
    name: "response.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("response attachment")
  });
  await expect(page.getByText("response.txt")).toBeVisible();
  await page.getByRole("button", { name: "Отправить отклик" }).click();
  await expect(page.getByText("Отклик отправлен")).toBeVisible();

  await logout(page);
  await loginAs(page, "Администратор платформы");

  await page.getByRole("link", { name: /Отклики/ }).click();
  await expect(page.getByRole("heading", { name: "Очередь откликов" })).toBeVisible();
  const projectFilter = page.getByRole("combobox", { name: "Проект" });
  await projectFilter.fill(projectTitle);
  const projectFilterOption = page.getByRole("option", { name: projectTitle });
  await expect(projectFilterOption).toBeVisible();
  await projectFilterOption.click();

  const responseRow = page.getByRole("row", { name: new RegExp(escapeRegExp(responseName)) });
  await expect(responseRow).toBeVisible();
  await expect(responseRow.getByText("response.txt")).toBeVisible();
  await responseRow.getByRole("combobox").selectOption("accepted");
  await expect(responseRow.getByRole("cell", { name: "Принят" }).first()).toBeVisible();

  await logout(page);
  await loginAs(page, "Сотрудник");

  await page.getByRole("link", { name: /Мои проекты/ }).click();
  await expect(page.getByRole("heading", { name: "Мои проекты" })).toBeVisible();
  await page.getByLabel("Поиск").fill(projectTitle);
  await page.getByRole("link", { name: new RegExp(escapeRegExp(projectTitle)) }).click();
  await expect(page.getByRole("heading", { level: 1, name: projectTitle })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Откликнуться на проект" })).toHaveCount(0);

  await logout(page);
  await loginAs(page, "Администратор платформы");

  await page.getByRole("link", { name: /Статистика/ }).click();
  await expect(page.getByRole("heading", { name: "Статистика витрины" })).toBeVisible();
  await expect(page.getByRole("row", { name: new RegExp(`${escapeRegExp(projectTitle)}\\s+1`) })).toBeVisible();
});
