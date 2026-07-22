import {
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
} from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";

const root = resolve(import.meta.dirname, "..", "..");
const expectedDirectory = resolve(root, "contracts/openapi");
const temporaryDirectory = mkdtempSync(resolve(tmpdir(), "prom-contracts-"));
const temporaryOpenApiDirectory = resolve(temporaryDirectory, "openapi");
const temporaryGeneratedDirectory = resolve(temporaryDirectory, "generated");
const expectedGeneratedDirectory = resolve(root, "contracts/generated/src");
const expectedFiles = [
  "access-service.openapi.json",
  "projects.openapi.json",
  "service-desk.openapi.json",
];
const expectedGeneratedFiles = ["access.ts", "projects.ts", "serviceDesk.ts"];

for (const entry of readdirSync(resolve(root, "apps"), {
  withFileTypes: true,
})) {
  if (!entry.isDirectory()) continue;
  const registrationPath = resolve(
    root,
    "apps",
    entry.name,
    "platform",
    "registration.json",
  );
  if (!existsSync(registrationPath)) continue;
  const registration = JSON.parse(readFileSync(registrationPath, "utf8"));
  expectedFiles.push(registration.openapiFile);
  expectedGeneratedFiles.push(registration.generatedFile);
}

try {
  const generate = spawnSync(
    process.execPath,
    [
      resolve(root, "tools/contracts/generate.mjs"),
      "--output",
      temporaryOpenApiDirectory,
      "--generated-output",
      temporaryGeneratedDirectory,
    ],
    { cwd: root, encoding: "utf8", env: process.env },
  );
  if (generate.status !== 0)
    throw new Error(generate.stderr || generate.stdout);

  const unexpectedFiles = readdirSync(expectedDirectory).filter(
    (file) => !expectedFiles.includes(file),
  );
  if (unexpectedFiles.length)
    throw new Error(`Unexpected contract files: ${unexpectedFiles.join(", ")}`);

  for (const file of expectedFiles) {
    const committed = JSON.parse(
      readFileSync(resolve(expectedDirectory, file), "utf8"),
    );
    const generated = JSON.parse(
      readFileSync(resolve(temporaryOpenApiDirectory, file), "utf8"),
    );
    if (!committed.openapi?.startsWith("3."))
      throw new Error(`${file} is not OpenAPI v3`);
    if (JSON.stringify(committed) !== JSON.stringify(generated)) {
      throw new Error(`${file} is stale; run npm run generate:contracts`);
    }
  }
  for (const file of expectedGeneratedFiles) {
    const committed = readFileSync(
      resolve(expectedGeneratedDirectory, file),
      "utf8",
    );
    const generated = readFileSync(
      resolve(temporaryGeneratedDirectory, file),
      "utf8",
    );
    if (committed !== generated) {
      throw new Error(`${file} is stale; run npm run generate:contracts`);
    }
  }
  console.log("OpenAPI contracts are current.");
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true });
}
