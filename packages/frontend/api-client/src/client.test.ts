import { describe, expect, it } from "vitest";

import { normalizeApiErrorMessage } from "./client";

describe("normalizeApiErrorMessage", () => {
  it("renders FastAPI validation errors as readable text", () => {
    const message = normalizeApiErrorMessage({
      detail: [
        {
          loc: ["body", "full_name"],
          msg: "String should have at least 2 characters",
          type: "string_too_short",
        },
      ],
    });

    expect(message).toBe("ФИО: укажите ФИО не короче 2 символов");
  });

  it("does not stringify object details as [object Object]", () => {
    const message = normalizeApiErrorMessage({
      detail: [
        {
          loc: ["body", "email"],
          msg: "Value error, Разрешены только email на домене @utmn.ru",
        },
      ],
    });

    expect(message).toBe("Email: Разрешены только email на домене @utmn.ru");
  });

  it("localizes short project field validation errors", () => {
    const message = normalizeApiErrorMessage({
      detail: [
        {
          loc: ["body", "title"],
          msg: "String should have at least 3 characters",
          type: "string_too_short",
          ctx: { min_length: 3 },
        },
      ],
    });

    expect(message).toBe("Название: заполните поле минимум 3 символами");
  });

  it("localizes project contact email validation errors", () => {
    const message = normalizeApiErrorMessage({
      detail: [
        {
          loc: ["body", "contact_email"],
          msg: "Value error, Разрешены только email на домене @utmn.ru",
          type: "value_error",
        },
      ],
    });

    expect(message).toBe(
      "Контактный email: Разрешены только email на домене @utmn.ru",
    );
  });

  it("localizes enum validation errors from project select fields", () => {
    const message = normalizeApiErrorMessage({
      detail: [
        {
          loc: ["body", "priority"],
          msg: "Input should be 'low', 'medium', 'high' or 'critical'",
          type: "enum",
          ctx: { expected: "'low', 'medium', 'high' or 'critical'" },
        },
      ],
    });

    expect(message).toBe(
      "Приоритет: выберите значение из списка: Низкий, Средний, Высокий, Критичный",
    );
  });

  it("does not expose unknown English validation messages", () => {
    const message = normalizeApiErrorMessage({
      detail: [
        {
          loc: ["query", "status"],
          msg: "Input should be a valid string",
          type: "string_type",
        },
      ],
    });

    expect(message).toBe("Статус: некорректное значение");
  });
});
