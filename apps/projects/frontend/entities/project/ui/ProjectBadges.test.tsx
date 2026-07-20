import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ProjectPriorityBadge } from "./ProjectPriorityBadge";
import { ProjectStatusBadge } from "./ProjectStatusBadge";

describe("project badges", () => {
  it("renders readable project status labels", () => {
    const html = renderToStaticMarkup(<ProjectStatusBadge status="active" />);

    expect(html).toContain("Активен");
    expect(html).toContain("badge-success");
  });

  it("renders readable project priority labels", () => {
    const html = renderToStaticMarkup(
      <ProjectPriorityBadge priority="critical" />,
    );

    expect(html).toContain("Критичный");
    expect(html).toContain("badge-danger");
  });
});
