import { describe, expect, it } from "vitest";

import type { ProjectDetails } from "../../../entities/project/model/types";
import type { ProjectResponse } from "../../../entities/project-response/model/types";
import { getProjectManagementMetrics } from "./AdminProjectManagePage";

const project: ProjectDetails = {
  id: "11111111-1111-1111-1111-111111111111",
  title: "Managed project",
  short_description: "Project summary",
  description: "Project description",
  goal: "Project goal",
  expected_result: null,
  project_type: "strategic",
  priority: "high",
  status: "active",
  start_date: null,
  end_date: null,
  responsible: null,
  contact_email: null,
  required_competencies: null,
  competency_blocks: [],
  competency_coverage: [],
  responses_count: 5,
  members: [
    {
      id: "22222222-2222-2222-2222-222222222222",
      full_name: "Member One",
      email: "member@utmn.ru",
      member_role: "working_group_member"
    },
    {
      id: "33333333-3333-3333-3333-333333333333",
      full_name: "Manager One",
      email: "manager@utmn.ru",
      member_role: "manager"
    }
  ],
  attachments: [
    {
      id: "44444444-4444-4444-4444-444444444444",
      owner_type: "project",
      owner_id: "11111111-1111-1111-1111-111111111111",
      file_name: "brief.pdf",
      content_type: "application/pdf",
      size_bytes: 120,
      download_url: "/api/attachments/44444444-4444-4444-4444-444444444444",
      created_at: "2026-07-03T12:00:00Z"
    }
  ],
  planned_tasks: null,
  created_at: "2026-07-03T12:00:00Z",
  updated_at: "2026-07-03T12:00:00Z"
};

function response(id: string, status: ProjectResponse["status"]): ProjectResponse {
  return {
    id,
    project_id: project.id,
    project_title: project.title,
    full_name: "Employee",
    email: "employee@utmn.ru",
    comment: null,
    competencies: null,
    attachments: [],
    status,
    created_at: "2026-07-03T12:00:00Z"
  };
}

describe("getProjectManagementMetrics", () => {
  it("counts response queue, accepted responses, files and working group", () => {
    const metrics = getProjectManagementMetrics(project, [
      response("1", "new"),
      response("2", "viewed"),
      response("3", "contacted"),
      response("4", "accepted"),
      response("5", "cancelled")
    ]);

    expect(metrics).toEqual({
      totalResponses: 5,
      newResponses: 1,
      acceptedResponses: 1,
      activeQueue: 3,
      workingGroupSize: 1,
      projectFiles: 1
    });
  });
});
