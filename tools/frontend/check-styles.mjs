import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..", "..");
const files = {
  global: resolve(root, "apps/platform-shell/src/app/styles/globals.css"),
  layout: resolve(root, "packages/frontend/layout/src/styles.css"),
  ui: resolve(root, "packages/frontend/ui/src/styles.css"),
  projectsFoundation: resolve(
    root,
    "apps/projects/frontend/platform-foundation.css",
  ),
  projects: resolve(root, "apps/projects/frontend/styles.css"),
  serviceDesk: resolve(root, "apps/service-desk/frontend/styles.css"),
};
const globalCss = readFileSync(files.global, "utf8");
const globalLines = globalCss.split(/\r?\n/).length;

if (globalLines > 120) {
  throw new Error(
    `Platform global CSS is too large: ${globalLines} lines (budget: 120)`,
  );
}
if (
  /\.service-desk-|\.project-(?:card|management|tasks|candidates|stream)|\.button|\.card|\.modal/.test(
    globalCss,
  )
) {
  throw new Error(
    "Component or product selectors remain in the platform global stylesheet",
  );
}
if (!globalCss.startsWith('@import "tailwindcss";')) {
  throw new Error(
    "Platform stylesheet must start with the Tailwind CSS import",
  );
}

const budgets = {
  global: 4_000,
  layout: 24_000,
  ui: 28_000,
  projectsFoundation: 10_000,
  projects: 55_000,
  serviceDesk: 75_000,
};
for (const [name, path] of Object.entries(files)) {
  const bytes = statSync(path).size;
  if (bytes > budgets[name]) {
    throw new Error(`${name} CSS is ${bytes} bytes (budget: ${budgets[name]})`);
  }
  console.log(`${name} CSS: ${bytes} bytes`);
}
