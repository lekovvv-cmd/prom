import { readdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const authRoot = resolve("packages/frontend/auth");
const forbidden = [
  "@prom/generated-contracts/projects",
  "@prom/projects-frontend",
  "ProjectsContract",
  "canManageProjects",
  "toLegacyUser",
  "UserProfilePayload",
];

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) return sourceFiles(path);
      return /\.[cm]?[jt]sx?$/.test(entry.name) ? [path] : [];
    }),
  );
  return nested.flat();
}

const violations = [];
for (const path of await sourceFiles(authRoot)) {
  const source = await readFile(path, "utf8");
  for (const value of forbidden) {
    if (source.includes(value)) violations.push(`${path}: ${value}`);
  }
  if (/\bprojects\.[\w.]+/.test(source)) {
    violations.push(`${path}: Projects permission or business logic`);
  }
}

if (violations.length) {
  console.error(
    "@prom/auth must remain independent of the Projects bounded context:",
  );
  console.error(violations.join("\n"));
  process.exitCode = 1;
}
