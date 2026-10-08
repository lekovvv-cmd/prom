import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { ResponseStatusSelect } from "./ResponseStatusSelect";

describe("ResponseStatusSelect", () => {
  it("shows only backend-permitted next statuses", () => {
    const html = renderToStaticMarkup(
      <ResponseStatusSelect
        responseId="response-1"
        value="contacted"
        onUpdated={vi.fn()}
      />,
    );
    expect(html).toContain('value="accepted"');
    expect(html).toContain('value="rejected"');
    expect(html).not.toContain('value="new"');
    expect(html).not.toContain('value="viewed"');
  });

  it("disables the selector after a final decision", () => {
    const html = renderToStaticMarkup(
      <ResponseStatusSelect
        responseId="response-1"
        value="accepted"
        onUpdated={vi.fn()}
      />,
    );
    expect(html).toContain("disabled");
    expect(html).not.toContain('value="rejected"');
  });
});
