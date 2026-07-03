import { describe, expect, it } from "vitest";

import { emptyProjectForm, normalizeProjectPayload, validateProjectForm } from "./ProjectFormFields";

describe("normalizeProjectPayload", () => {
  it("converts empty optional form fields to null", () => {
    const payload = normalizeProjectPayload({
      ...emptyProjectForm,
      title: "Test",
      short_description: "Short",
      description: "Long",
      goal: "Goal",
      expected_result: "",
      contact_email: "",
      required_competencies: "",
      planned_tasks: ""
    });

    expect(payload.expected_result).toBeNull();
    expect(payload.contact_email).toBeNull();
    expect(payload.required_competencies).toBeNull();
    expect(payload.planned_tasks).toBeNull();
  });

  it("keeps selected responsible user id", () => {
    const payload = normalizeProjectPayload({
      ...emptyProjectForm,
      title: "Test",
      short_description: "Short",
      description: "Long",
      goal: "Goal",
      responsible_user_id: "3f9c19e3-f3c0-4f98-89b8-12ac1f5e5ec2"
    });

    expect(payload.responsible_user_id).toBe("3f9c19e3-f3c0-4f98-89b8-12ac1f5e5ec2");
  });

  it("keeps selected working group member ids", () => {
    const payload = normalizeProjectPayload({
      ...emptyProjectForm,
      title: "Test",
      short_description: "Short",
      description: "Long",
      goal: "Goal",
      working_group_member_ids: [
        "3f9c19e3-f3c0-4f98-89b8-12ac1f5e5ec2",
        "a3f99d22-6816-42c8-960d-9bc521e4ef1a"
      ]
    });

    expect(payload.working_group_member_ids).toEqual([
      "3f9c19e3-f3c0-4f98-89b8-12ac1f5e5ec2",
      "a3f99d22-6816-42c8-960d-9bc521e4ef1a"
    ]);
  });
});

describe("validateProjectForm", () => {
  it("rejects empty required fields even without browser required attributes", () => {
    expect(validateProjectForm({ ...emptyProjectForm, title: " " })).toBe(
      "Название: заполните поле минимум 3 символами"
    );
  });

  it("accepts filled required fields", () => {
    expect(
      validateProjectForm({
        ...emptyProjectForm,
        title: "Проект",
        short_description: "Краткое описание",
        description: "Полное описание",
        goal: "Цель проекта"
      })
    ).toBeNull();
  });

  it("rejects invalid contact email before submit", () => {
    expect(
      validateProjectForm({
        ...emptyProjectForm,
        title: "Проект",
        short_description: "Краткое описание",
        description: "Полное описание",
        goal: "Цель проекта",
        contact_email: "manager@example.com"
      })
    ).toBe("Контактный email: введите корректный адрес на домене @utmn.ru");
  });
});
