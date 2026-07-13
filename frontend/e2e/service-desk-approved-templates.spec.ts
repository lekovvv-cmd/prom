import { expect, test, type Page } from "@playwright/test";

import { loginAs, watchPage } from "./helpers";

type ApprovedTemplate = {
  category: string;
  service: string;
  labels: string[];
};

const approvedTemplates: ApprovedTemplate[] = [
  { category: "ГИА: Администрирование", service: "Заказ воды", labels: ["Количество бутылок", "Объем бутылок", "Тип воды", "Дата и время начала мероприятия", "Дата и время окончания мероприятия", "Количество членов комиссии", "Количество заседаний ГЭК", "Количество выпускающихся студентов"] },
  { category: "ГИА: Администрирование", service: "Установка камер", labels: ["Институт", "Вид ГИА", "Направление (специальность)", "Адрес установки камер", "Номер аудитории для установки камер", "Дата и время начала мероприятия", "Дата и время окончания мероприятия", "комментарии"] },
  { category: "Административно-хозяйственное сопровождение", service: "Бронирование аудиторий", labels: ["Цель брони аудитории", "ФИО (с кем согласовано)", "Адрес корпуса брони аудитории", "Номер аудитории", "Дата и время начала мероприятия", "Дата и время окончания мероприятия", "Комментарий"] },
  { category: "Административно-хозяйственное сопровождение", service: "На печать в Издательство", labels: ["Название мероприятия", "Согласовано/не согласовано с издательством", "Вид продукции", "Сроки изготовления", "Количество продукции", "Ссылка на шаблон", "Дополнительные характеристики"] },
  { category: "Административно-хозяйственное сопровождение", service: "Роль табельщика (табель рабочего времени, график отпусков)", labels: ["ФИО", "Дата начала отпуска", "Дата окончания отпуска"] },
  { category: "Административно-хозяйственное сопровождение", service: "Ввоз (вывоз) и внос (вынос) материальных ценностей", labels: ["Название мероприятия", "Дата и время вноса (ввоза)", "Дата и время выноса (вывоза)", "Прикрепите файл с перечнем МЦ", "Вид материальных ценностей", "Тара", "Номер, модель ТС при ввозе (вывозе)"] },
  { category: "Административно-хозяйственное сопровождение", service: "Допуск в здание", labels: ["ФИО (на кого оформляется допуск)", "Оборудование", "Адрес", "Дата начала доступа", "Дата прекращения доступа"] },
  { category: "Административно-хозяйственное сопровождение", service: "Транспортное обслуживание", labels: ["Название мероприятия", "Количество человек (всего)", "Количество студентов", "Дата и время начала мероприятия", "Дата и время окончания мероприятия", "Маршрут (откуда-куда)"] },
  { category: "Административно-хозяйственное сопровождение", service: "Оформление и регистрация исходящего документа", labels: ["Документ", "Проект или скан документа"] },
  { category: "Административно-хозяйственное сопровождение", service: "График отпусков", labels: ["ФИО", "Дата начала отпуска", "Дата окончания отпуска"] },
  { category: "Административно-хозяйственное сопровождение", service: "Получение со склада (кроме компьютерной техники)", labels: ["Материально ответственное лицо ФИО", "Должность", "Мероприятие", "Список для выдачи со склада"] },
];

async function openTemplate(page: Page, template: ApprovedTemplate) {
  await page.goto("/service-desk");
  const category = page.getByRole("region", { name: template.category, exact: true });
  const serviceHeading = category.getByRole("heading", { name: template.service, exact: true });
  await expect(serviceHeading).toBeVisible();
  await serviceHeading.locator("xpath=../..").getByRole("link", { name: "Открыть услугу" }).click();
  await expect(page.getByRole("heading", { level: 1, name: template.service })).toBeVisible();
}

async function fillCommon(page: Page, title: string) {
  await page.getByLabel("Тема заявки").fill(title);
  await page.getByLabel("Описание").fill("E2E-проверка утверждённого шаблона.");
}

async function submit(page: Page) {
  await page.getByRole("button", { name: "Отправить заявку" }).click();
  await expect(page).toHaveURL(/\/service-desk\/tickets\//);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(/^SD-/);
}

test("all eleven approved templates render exact labels and reject an empty submission", async ({ page }) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Менеджер Service Desk", "/service-desk");

  for (const template of approvedTemplates) {
    await openTemplate(page, template);
    for (const label of template.labels) {
      const field = label === "Документ" ? page.locator("#document") : page.getByLabel(label);
      await expect(field).toBeVisible();
    }
    await page.getByRole("button", { name: "Отправить заявку" }).click();
    await expect(page.getByText("Заполните обязательные поля")).toBeVisible();
  }

  await openTemplate(page, approvedTemplates[0]);
  await expect(page.getByLabel("Вид ГИА")).toHaveCount(0);
  await expect(page.getByLabel("Дата доставки")).toHaveCount(0);
  diagnostics.assertClean();
});

test("approved templates submit with required dictionaries and files", async ({ page }) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  await loginAs(page, "Менеджер Service Desk", "/service-desk");

  await openTemplate(page, approvedTemplates[0]);
  await page.getByLabel("Количество бутылок").fill("12");
  await page.getByLabel("Объем бутылок").fill("0.5");
  await page.getByLabel("Тип воды").selectOption("still");
  await page.getByLabel("Дата и время начала мероприятия").fill("2027-01-15T09:00");
  await page.getByLabel("Дата и время окончания мероприятия").fill("2027-01-15T12:00");
  await page.getByLabel("Количество членов комиссии").fill("3");
  await page.getByLabel("Количество заседаний ГЭК").fill("1");
  await page.getByLabel("Количество выпускающихся студентов").fill("12");
  await fillCommon(page, `E2E вода ${suffix}`);
  await submit(page);
  await expect(page.getByText("Негазированная")).toBeVisible();

  await openTemplate(page, approvedTemplates[1]);
  await expect(page.getByLabel("Институт")).toHaveValue("shpiu");
  await expect(page.getByLabel("Адрес установки камер")).toHaveValue("lenina_38");
  await page.getByLabel("Вид ГИА").selectOption("state_exam");
  await page.getByLabel("Направление (специальность)").selectOption("40_03_01_law");
  await page.getByLabel("Номер аудитории для установки камер").fill("305");
  await page.getByLabel("Дата и время начала мероприятия").fill("2027-01-15T09:00");
  await page.getByLabel("Дата и время окончания мероприятия").fill("2027-01-15T12:00");
  await fillCommon(page, `E2E камеры ${suffix}`);
  await submit(page);

  await openTemplate(page, approvedTemplates[2]);
  await page.getByLabel("Цель брони аудитории").fill("Защита ВКР");
  await page.getByLabel("ФИО (с кем согласовано)").fill("Иванова И.И.");
  await page.getByLabel("Адрес корпуса брони аудитории").selectOption("lenina_16");
  await page.getByLabel("Номер аудитории").fill("305");
  await page.getByLabel("Дата и время начала мероприятия").fill("2027-01-15T09:00");
  await page.getByLabel("Дата и время окончания мероприятия").fill("2027-01-15T12:00");
  await fillCommon(page, `E2E бронь ${suffix}`);
  await submit(page);

  await openTemplate(page, approvedTemplates[3]);
  await page.getByLabel("Название мероприятия").fill("День открытых дверей");
  await page.getByLabel("Согласовано/не согласовано с издательством").selectOption("approved");
  await page.getByLabel("Вид продукции").fill("Буклет");
  await page.getByLabel("Сроки изготовления").fill("2027-01-14");
  await page.getByLabel("Количество продукции").fill("100");
  await page.getByLabel("Ссылка на шаблон").fill("внутренний шаблон");
  await fillCommon(page, `E2E печать ${suffix}`);
  await submit(page);

  await openTemplate(page, approvedTemplates[5]);
  await page.getByLabel("Название мероприятия").fill("Конференция");
  await page.getByLabel("Дата и время вноса (ввоза)").fill("2027-01-15T08:00");
  await page.getByLabel("Дата и время выноса (вывоза)").fill("2027-01-15T18:00");
  await page.locator("#inventory_list_file").setInputFiles({ name: "inventory.txt", mimeType: "text/plain", buffer: Buffer.from("Inventory") });
  await page.getByLabel("Вид материальных ценностей").fill("Стенды");
  await page.getByLabel("Тара").fill("Коробки");
  await page.getByLabel("Номер, модель ТС при ввозе (вывозе)").fill("А123АА, Газель");
  await fillCommon(page, `E2E МЦ ${suffix}`);
  await submit(page);
  await expect(page.getByText("Прикрепите файл с перечнем МЦ: inventory.txt", { exact: true })).toBeVisible();

  await openTemplate(page, approvedTemplates[8]);
  await page.locator("#document").fill("Служебная записка");
  await page.locator("#document_file").setInputFiles({ name: "document.txt", mimeType: "text/plain", buffer: Buffer.from("Document") });
  await fillCommon(page, `E2E исходящий ${suffix}`);
  await submit(page);
  await expect(page.getByText("Проект или скан документа: document.txt", { exact: true })).toBeVisible();

  await openTemplate(page, approvedTemplates[10]);
  await page.getByLabel("Материально ответственное лицо ФИО").fill("Петров П.П.");
  await page.getByLabel("Должность").fill("Специалист");
  await page.getByLabel("Мероприятие").fill("Обустройство аудитории");
  await page.locator("#inventory_list_file").setInputFiles({ name: "warehouse.txt", mimeType: "text/plain", buffer: Buffer.from("Warehouse") });
  await fillCommon(page, `E2E склад ${suffix}`);
  await submit(page);
  await expect(page.getByText("Список для выдачи со склада: warehouse.txt", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Список для выдачи со склада: warehouse.txt", { exact: true })).toBeVisible();

  diagnostics.assertClean();
});
