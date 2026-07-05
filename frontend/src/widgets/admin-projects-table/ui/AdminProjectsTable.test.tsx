import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { Project } from "../../../entities/project/model/types";
import { AdminProjectsTable } from "./AdminProjectsTable";

const archivedProject: Project = {
  id: "11111111-1111-1111-1111-111111111111",
  title: "Archived project",
  short_description: "Hidden from current list",
  goal: "Keep row in database",
  project_type: "strategic",
  priority: "low",
  status: "archived",
  start_date: null,
  end_date: null,
  responsible: null,
  required_competencies: null,
  competency_blocks: [],
  responses_count: 0,
  created_at: "2026-07-03T12:00:00Z"
};

describe("AdminProjectsTable", () => {
  it("shows delete action in archive view", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <AdminProjectsTable
          projects={[archivedProject]}
          onEdit={vi.fn()}
          onArchived={vi.fn()}
          isArchiveView
        />
      </MemoryRouter>
    );

    expect(html).toContain(`/admin/projects/${archivedProject.id}`);
    expect(html).toContain("Открыть");
    expect(html).toContain("Вернуть");
    expect(html).toContain("Удалить");
  });
});
