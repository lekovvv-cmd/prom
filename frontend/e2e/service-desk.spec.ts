import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const serviceDeskUrl = process.env.E2E_SERVICE_DESK_URL ?? "http://127.0.0.1:8001";

async function loginAsManager(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: /Руководитель/ }).click();
  await page.getByRole("button", { name: /^Войти$/ }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(
    page.getByRole("banner").getByRole("link", { name: /manager@utmn\.ru/ })
  ).toBeVisible();
  const token = await page.evaluate(() => localStorage.getItem("shpiu_project_showcase_token"));
  expect(token).toBeTruthy();
  return token as string;
}

async function loginAsEmployee(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: /Сотрудник/ }).click();
  await page.getByRole("button", { name: /^Войти$/ }).click();
  await expect(page).toHaveURL(/\/projects$/);
}

async function serviceDeskRequest<T>(
  request: APIRequestContext,
  token: string,
  method: "get" | "post" | "put",
  path: string,
  data?: unknown
) {
  const response = await request[method](`${serviceDeskUrl}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    data
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()) as T;
}

test("Service Desk flow: approver reviews and approves a ticket", async ({ page, request }) => {
  const token = await loginAsManager(page);
  const currentUser = await serviceDeskRequest<{ id: string }>(request, token, "get", "/me");
  const suffix = Date.now();

  const category = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    "/admin/categories",
    { title: `E2E approval category ${suffix}` }
  );
  const service = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    "/admin/services",
    { category_id: category.id, title: `E2E approval service ${suffix}` }
  );
  const version = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    `/admin/services/${service.id}/versions`
  );
  const configured = await serviceDeskRequest<{ workflow: { id: string } }>(
    request,
    token,
    "put",
    `/admin/template-versions/${version.id}/approval-workflow`,
    { approval_mode: "workflow", name: "E2E согласование" }
  );
  await serviceDeskRequest(
    request,
    token,
    "post",
    `/admin/approval-workflows/${configured.workflow.id}/stages`,
    { title: "Согласование руководителя", decision_rule: "any" }
  );
  const workflow = await serviceDeskRequest<{
    workflow: { stages: Array<{ id: string; title: string }> };
  }>(request, token, "get", `/admin/template-versions/${version.id}/approval-workflow`);
  const stageId = workflow.workflow.stages.find(
    (item) => item.title === "Согласование руководителя"
  )?.id;
  expect(stageId).toBeTruthy();
  await serviceDeskRequest(
    request,
    token,
    "post",
    `/admin/approval-stages/${stageId}/approvers`,
    { service_desk_user_id: currentUser.id }
  );
  await serviceDeskRequest(
    request,
    token,
    "post",
    `/admin/template-versions/${version.id}/publish`
  );

  const draft = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    "/tickets/drafts",
    {
      service_id: service.id,
      title: `E2E заявка ${suffix}`,
      description: "Проверка защищённого UI согласования."
    }
  );
  const ticket = await serviceDeskRequest<{ id: string; number: string }>(
    request,
    token,
    "post",
    `/tickets/${draft.id}/submit`
  );

  await page.goto(`/service-desk/tickets/${ticket.id}`);
  await expect(page.getByRole("heading", { level: 1, name: ticket.number })).toBeVisible();
  await expect(page.getByLabel("Счётчики Service Desk").getByText("Моё согласование")).toBeVisible();
  await expect(page.getByLabel("Счётчики Service Desk").getByText("SLA breaches")).toBeVisible();
  await expect(page.getByRole("heading", { name: `E2E заявка ${suffix}` })).toBeVisible();
  await expect(page.getByText("На согласовании")).toBeVisible();
  await expect(page.getByRole("button", { name: "Согласовать" })).toBeVisible();

  await page.getByRole("button", { name: "Уведомления Service Desk" }).click();
  const notificationCenter = page.getByRole("region", { name: "Центр уведомлений" });
  await expect(notificationCenter.getByText("Требуется согласование")).toBeVisible();
  await expect(notificationCenter.getByRole("link", { name: "Открыть заявку" }).first()).toHaveAttribute(
    "href", `/service-desk/tickets/${ticket.id}`
  );
  await notificationCenter.getByRole("button", { name: "Прочитать все" }).click();
  await expect(notificationCenter.getByText("Всё прочитано")).toBeVisible();

  await page.getByRole("button", { name: "Согласовать" }).click();
  const dialog = page.getByRole("dialog", { name: "Согласовать заявку" });
  await dialog.getByLabel("Комментарий").fill("E2E: согласовано");
  await dialog.getByRole("button", { name: "Подтвердить согласование" }).click();

  await expect(dialog).toBeHidden();
  await expect(page.getByText("Согласована")).toBeVisible();
  await expect(page.locator(".service-desk-approvals").getByText("E2E: согласовано")).toBeVisible();
  await expect(page.getByRole("button", { name: "Согласовать" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Отклонить" })).toHaveCount(0);
});

test("Service Desk SLA admin persists complete calendar, policy, binding and escalation edits", async ({ page, request }) => {
  const token = await loginAsManager(page);
  const suffix = Date.now();
  await page.goto("/service-desk/admin/sla");
  await expect(page.getByRole("heading", { name: "SLA Service Desk" })).toBeVisible();
  const calendarName = `E2E SLA calendar ${suffix}`;
  const policyName = `E2E SLA policy ${suffix}`;
  const bindingName = `E2E SLA binding ${suffix}`;
  const calendarSection = page.locator('section[aria-labelledby="sla-calendars-title"]');
  const calendarForm = calendarSection.locator("form");
  await calendarForm.getByLabel("Название").fill(calendarName);
  await calendarForm.getByLabel("День недели 1").selectOption("5");
  await calendarForm.getByLabel("Начало интервала 1").fill("10:00");
  await calendarForm.getByLabel("Конец интервала 1").fill("13:00");
  await calendarForm.getByRole("button", { name: "Интервал", exact: true }).click();
  await calendarForm.getByLabel("День недели 2").selectOption("5");
  await calendarForm.getByLabel("Начало интервала 2").fill("14:00");
  await calendarForm.getByLabel("Конец интервала 2").fill("16:00");
  await calendarForm.getByRole("button", { name: "Исключение", exact: true }).click();
  await calendarForm.getByLabel("Дата исключения 1").fill("2027-01-01");
  await calendarForm.getByLabel("Описание исключения 1").fill("E2E holiday");
  await calendarForm.getByRole("button", { name: "Исключение", exact: true }).click();
  await calendarForm.getByLabel("Дата исключения 2").fill("2027-01-02");
  await calendarForm.getByLabel("Тип исключения 2").selectOption("custom_hours");
  await calendarForm.getByLabel("Начало исключения 2").fill("10:00");
  await calendarForm.getByLabel("Конец исключения 2").fill("12:00");
  await calendarForm.getByRole("button", { name: "Исключение", exact: true }).click();
  await calendarForm.getByLabel("Дата исключения 3").fill("2027-01-02");
  await calendarForm.getByLabel("Тип исключения 3").selectOption("custom_hours");
  await calendarForm.getByLabel("Начало исключения 3").fill("13:00");
  await calendarForm.getByLabel("Конец исключения 3").fill("15:00");
  await calendarForm.getByRole("button", { name: "Создать" }).click();

  const calendarCard = calendarSection.locator(".service-desk-sla-summary-card").filter({ hasText: calendarName });
  await expect(calendarCard).toContainText("2 интервалов · 3 исключений");
  await calendarCard.getByRole("button", { name: "Изменить" }).click();
  await calendarForm.getByLabel("Название").fill(`${calendarName} edited`);
  await calendarForm.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(calendarSection.getByText(`${calendarName} edited`)).toBeVisible();

  const policySection = page.locator('section[aria-labelledby="sla-policies-title"]');
  const policyForm = policySection.locator("form");
  await policyForm.getByLabel("Название").fill(policyName);
  await policyForm.getByLabel("Описание").fill("E2E critical policy");
  await policyForm.getByLabel("Бизнес-календарь").selectOption({ label: `${calendarName} edited` });
  await policyForm.getByLabel("First response, минут").fill("15");
  await policyForm.getByLabel("Resolution, минут").fill("240");
  await policyForm.getByLabel("Пауза: ожидание заявителя").check();
  await policyForm.getByRole("button", { name: "Создать" }).click();
  const policyCard = policySection.locator(".service-desk-sla-summary-card").filter({ hasText: policyName });
  await policyCard.getByRole("button", { name: "Изменить" }).click();
  await policyForm.getByLabel("Resolution, минут").fill("300");
  await policyForm.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(policyCard).toContainText("Resolution 300 мин");

  const bindingSection = page.locator('section[aria-labelledby="sla-bindings-title"]');
  const bindingForm = bindingSection.locator("form");
  await bindingForm.getByLabel("Название").fill(bindingName);
  await bindingForm.getByLabel("SLA policy").selectOption({ label: policyName });
  await bindingForm.getByLabel("Тип условия 1").selectOption("priority");
  await bindingForm.getByLabel("Значение условия 1").selectOption("high");
  await bindingForm.getByRole("button", { name: "Условие", exact: true }).click();
  await bindingForm.getByLabel("Тип условия 2").selectOption("field_value");
  await bindingForm.getByLabel("Ключ поля 2").fill("impact");
  await bindingForm.getByLabel("Значение условия 2").fill("critical");
  await bindingForm.getByRole("button", { name: "Создать" }).click();
  const bindingCard = bindingSection.locator(".service-desk-sla-summary-card").filter({ hasText: bindingName });
  await expect(bindingCard).toContainText("2 условий");
  await bindingCard.getByRole("button", { name: "Изменить" }).click();
  await bindingForm.getByLabel("Приоритет").fill("12");
  await bindingForm.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(bindingCard).toContainText("Приоритет 12");

  const escalationSection = page.locator('section[aria-labelledby="sla-escalations-title"]');
  const escalationForm = escalationSection.locator("form");
  await escalationForm.getByLabel("SLA policy").selectOption({ label: policyName });
  await escalationForm.getByLabel("Threshold, %").fill("73");
  await escalationForm.getByLabel("Получатель").selectOption("specific_user");
  await escalationForm.getByLabel("Пользователь-получатель").selectOption({ label: "Manager — manager@utmn.ru" });
  await escalationForm.getByRole("button", { name: "Создать" }).click();
  const escalationCard = escalationSection.locator(".service-desk-sla-summary-card").filter({ hasText: "resolution · 73%" });
  await expect(escalationCard).toContainText("specific_user");
  await escalationCard.getByRole("button", { name: "Изменить" }).click();
  await escalationForm.getByLabel("Threshold, %").fill("81");
  await escalationForm.getByRole("button", { name: "Сохранить изменения" }).click();

  await page.reload();
  await expect(page.getByText(`${calendarName} edited`)).toBeVisible();
  await expect(page.getByText("resolution · 81%")).toBeVisible();
  const calendars = await serviceDeskRequest<Array<{ name: string; business_hours: unknown[]; exceptions: Array<{ type: string }> }>>(
    request, token, "get", "/admin/sla/calendars"
  );
  const calendar = calendars.find((item) => item.name === `${calendarName} edited`);
  expect(calendar?.business_hours).toHaveLength(2);
  expect(calendar?.exceptions.filter((item) => item.type === "custom_hours")).toHaveLength(2);
  const bindings = await serviceDeskRequest<Array<{ name: string; priority: number; conditions: Array<{ field: string; field_key?: string }> }>>(
    request, token, "get", "/admin/sla/bindings"
  );
  expect(bindings.find((item) => item.name === bindingName)).toMatchObject({
    priority: 12,
    conditions: [
      { field: "priority" },
      { field: "field_value", field_key: "impact" }
    ]
  });

  const persistedEscalationCard = escalationSection.locator(".service-desk-sla-summary-card").filter({ hasText: "resolution · 81%" });
  page.once("dialog", (dialog) => dialog.accept());
  await persistedEscalationCard.getByRole("button", { name: "Удалить" }).click();
  await expect(persistedEscalationCard).toHaveCount(0);
});

test("Service Desk Workbench assigns, starts and resolves a ticket", async ({ page, request }) => {
  const token = await loginAsManager(page);
  const assignees = await serviceDeskRequest<Array<{ id: string; display_name: string }>>(
    request, token, "get", "/workbench/users?eligible_assignees=true"
  );
  const employee = assignees.find((item) => item.display_name === "Сотрудник ШПИУ");
  expect(employee).toBeTruthy();
  const suffix = Date.now();
  const category = await serviceDeskRequest<{ id: string }>(request, token, "post", "/admin/categories", { title: `E2E Workbench ${suffix}` });
  const service = await serviceDeskRequest<{ id: string }>(request, token, "post", "/admin/services", { category_id: category.id, title: `E2E Workbench service ${suffix}` });
  const version = await serviceDeskRequest<{ id: string }>(request, token, "post", `/admin/services/${service.id}/versions`);
  await serviceDeskRequest(request, token, "post", `/admin/template-versions/${version.id}/publish`);
  const draft = await serviceDeskRequest<{ id: string }>(request, token, "post", "/tickets/drafts", {
    service_id: service.id,
    title: `E2E Workbench ticket ${suffix}`,
    description: "Проверка критического Workbench flow."
  });
  const ticket = await serviceDeskRequest<{ id: string; number: string }>(request, token, "post", `/tickets/${draft.id}/submit`);

  await page.goto("/service-desk/workbench");
  await expect(page.getByRole("heading", { name: "Рабочее место Service Desk" })).toBeVisible();
  const row = page.getByRole("row").filter({ hasText: `E2E Workbench ticket ${suffix}` });
  await expect(row).toBeVisible();
  await row.getByLabel(`Действия ${ticket.number}`).selectOption("assign");
  let dialog = page.getByRole("dialog");
  await dialog.getByLabel("Исполнитель").selectOption(employee?.id);
  await dialog.getByRole("button", { name: "Подтвердить" }).click();
  await expect(row.getByText(employee?.display_name ?? "Сотрудник ШПИУ")).toBeVisible();

  await loginAsEmployee(page);
  await page.goto("/service-desk/workbench");
  const employeeRow = page.getByRole("row").filter({ hasText: `E2E Workbench ticket ${suffix}` });
  await employeeRow.getByLabel(`Действия ${ticket.number}`).selectOption("start");
  dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Подтвердить" }).click();
  await expect(employeeRow.getByText("В работе")).toBeVisible();

  await employeeRow.getByLabel(`Действия ${ticket.number}`).selectOption("resolve");
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Результат решения").fill("E2E Workbench выполнено");
  await dialog.getByRole("button", { name: "Подтвердить" }).click();
  await expect(employeeRow.getByText("Выполнена")).toBeVisible();
});
