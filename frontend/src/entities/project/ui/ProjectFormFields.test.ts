import { describe, expect, it } from "vitest";

import { emptyProjectForm, normalizeProjectPayload } from "./ProjectFormFields";

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
});
