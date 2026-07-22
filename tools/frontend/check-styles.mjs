import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { extname, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const sourceRoots = [
  resolve(root, "apps/platform-shell"),
  resolve(root, "apps/projects/frontend"),
  resolve(root, "apps/service-desk/frontend"),
  resolve(root, "packages/frontend"),
];
const ignoredSegments = new Set([
  "node_modules",
  "dist",
  "coverage",
  "test-results",
]);

function walk(directory, extensions) {
  if (!existsSync(directory)) return [];
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    if (ignoredSegments.has(entry.name)) return [];
    const path = resolve(directory, entry.name);
    return entry.isDirectory()
      ? walk(path, extensions)
      : extensions.has(extname(entry.name))
        ? [path]
        : [];
  });
}

const cssFiles = sourceRoots.flatMap((directory) =>
  walk(directory, new Set([".css"])),
);
const codeFiles = sourceRoots.flatMap((directory) =>
  walk(directory, new Set([".ts", ".tsx", ".html"])),
);
const violations = [];
const warnings = [];
const globalPath = resolve(
  root,
  "apps/platform-shell/src/app/styles/globals.css",
);
const deprecatedProductSheets = [
  resolve(root, "apps/projects/frontend/styles.css"),
  resolve(root, "apps/projects/frontend/platform-foundation.css"),
  resolve(root, "apps/service-desk/frontend/styles.css"),
];

for (const path of deprecatedProductSheets) {
  if (existsSync(path))
    violations.push(
      `Giant legacy stylesheet still exists: ${relative(root, path)}`,
    );
}

let totalLines = 0;
let totalBytes = 0;
let rawColors = 0;
let importantCount = 0;
let largest = { path: "", lines: 0 };
const classNames = new Set();
for (const path of cssFiles) {
  const content = readFileSync(path, "utf8");
  const lines = content.split(/\r?\n/).length;
  const relativePath = relative(root, path).replaceAll("\\", "/");
  const isGlobal = path === globalPath;
  const isTokenLayer = /(?:theme|tokens)\.css$/.test(relativePath);
  totalLines += lines;
  totalBytes += statSync(path).size;
  if (lines > largest.lines) largest = { path: relativePath, lines };
  if (isGlobal && lines > 150) {
    violations.push(`${relativePath}: ${lines} global lines (budget: 150)`);
  } else if (!isGlobal && lines > 500) {
    violations.push(`${relativePath}: ${lines} lines (budget: 500)`);
  } else if (!isGlobal && lines > 300) {
    warnings.push(`${relativePath}: ${lines} lines (warning threshold: 300)`);
  }
  const colors = content.match(/#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)/g) ?? [];
  rawColors += colors.length;
  if (colors.length && !isTokenLayer) {
    violations.push(
      `${relativePath}: ${colors.length} raw colors outside theme/tokens`,
    );
  }
  const important = content.match(/!important\b/g) ?? [];
  importantCount += important.length;
  if (important.length) {
    violations.push(
      `${relativePath}: undocumented !important (${important.length})`,
    );
  }
  if (
    relativePath.startsWith("apps/projects/frontend/") ||
    relativePath.startsWith("apps/service-desk/frontend/")
  ) {
    const forbidden = content.match(
      /(?:^|\})\s*\.(?:button|card|modal)(?=[\s,:>{\[])/gm,
    );
    if (forbidden)
      violations.push(
        `${relativePath}: product-level .button/.card/.modal definition`,
      );
  }
  const withoutUrls = content.replace(/url\([^)]*\)/g, "");
  for (const match of withoutUrls.matchAll(/\.([A-Za-z_][A-Za-z0-9_-]*)/g)) {
    classNames.add(match[1]);
  }
}

const globalCss = readFileSync(globalPath, "utf8");
if (!globalCss.startsWith('@import "tailwindcss";')) {
  violations.push(
    "Platform global stylesheet must start with the Tailwind CSS import",
  );
}

const code = codeFiles.map((path) => readFileSync(path, "utf8")).join("\n");
const dynamicPrefixes = new Set(
  [...code.matchAll(/([A-Za-z_][A-Za-z0-9_-]*-)\$\{/g)].map(
    (match) => match[1],
  ),
);
const unused = [...classNames]
  .filter((name) => {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (new RegExp(`(?<![A-Za-z0-9_-])${escaped}(?![A-Za-z0-9_-])`).test(code))
      return false;
    return ![...dynamicPrefixes].some((prefix) => name.startsWith(prefix));
  })
  .sort();
if (unused.length) {
  violations.push(`Unused CSS selectors: ${unused.join(", ")}`);
}

for (const warning of warnings) console.warn(`Style warning: ${warning}`);
if (violations.length) {
  throw new Error(`Style boundaries failed:\n- ${violations.join("\n- ")}`);
}

console.log(
  JSON.stringify(
    {
      cssFiles: cssFiles.length,
      globalLines: globalCss.split(/\r?\n/).length,
      totalLines,
      totalBytes,
      largest,
      unusedSelectors: unused.length,
      rawColors,
      importantCount,
      warnings: warnings.length,
    },
    null,
    2,
  ),
);
