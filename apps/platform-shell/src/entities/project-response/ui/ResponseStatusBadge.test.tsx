import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ResponseStatusBadge } from "./ResponseStatusBadge";

describe("ResponseStatusBadge", () => {
  it("renders contacted status in Russian", () => {
    const html = renderToStaticMarkup(<ResponseStatusBadge status="contacted" />);

    expect(html).toContain("Связались");
    expect(html).toContain("badge-info");
  });
});
