import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";

const root = resolve(import.meta.dirname, "..", "..");
const expectedDirectory = resolve(root, "contracts/openapi");
const temporaryDirectory = mkdtempSync(resolve(tmpdir(), "prom-contracts-"));
const expectedFiles = ["access-service.openapi.json", "projects.openapi.json", "service-desk.openapi.json"];

try {
  const generate = spawnSync(process.execPath, [resolve(root, "tools/contracts/generate.mjs"), "--output", temporaryDirectory], {
    cwd: root,
    encoding: "utf8",
    env: process.env,
  });
  if (generate.status !== 0) throw new Error(generate.stderr || generate.stdout);

  const unexpectedFiles = readdirSync(expectedDirectory).filter((file) => !expectedFiles.includes(file));
  if (unexpectedFiles.length) throw new Error(`Unexpected contract files: ${unexpectedFiles.join(", ")}`);

  for (const file of expectedFiles) {
    const committed = JSON.parse(readFileSync(resolve(expectedDirectory, file), "utf8"));
    const generated = JSON.parse(readFileSync(resolve(temporaryDirectory, file), "utf8"));
    if (!committed.openapi?.startsWith("3.")) throw new Error(`${file} is not OpenAPI v3`);
    if (JSON.stringify(committed) !== JSON.stringify(generated)) {
      throw new Error(`${file} is stale; run npm run generate:contracts`);
    }
  }
  console.log("OpenAPI contracts are current.");
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true });
}
