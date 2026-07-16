import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..", "..");
const outputFlag = process.argv.indexOf("--output");
const outputDir = resolve(root, outputFlag >= 0 ? process.argv[outputFlag + 1] : "contracts/openapi");
const python = process.env.PROM_PYTHON ?? (process.platform === "win32" ? "py" : "python");
const pythonPrefix = process.env.PROM_PYTHON ? [] : (process.platform === "win32" ? ["-3.14"] : []);

if (outputFlag >= 0 && !process.argv[outputFlag + 1]) {
  throw new Error("--output requires a directory");
}

const services = [
  {
    file: "access-service.openapi.json",
    cwd: root,
    bootstrap: "import sys; sys.path.insert(0, 'packages/python/platform-sdk/src'); sys.path.insert(0, 'apps/access-service/src'); from access_service.bootstrap.app import app",
  },
  {
    file: "projects.openapi.json",
    cwd: resolve(root, "apps/projects/backend"),
    bootstrap: "from app.main import app",
  },
  {
    file: "service-desk.openapi.json",
    cwd: resolve(root, "apps/service-desk/backend"),
    bootstrap: "from app.main import app",
  },
];

mkdirSync(outputDir, { recursive: true });
for (const service of services) {
  const result = spawnSync(
    python,
    [...pythonPrefix, "-c", `${service.bootstrap}; import json; print(json.dumps(app.openapi(), ensure_ascii=False, sort_keys=True, indent=2))`],
    { cwd: service.cwd, encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" } },
  );
  if (result.status !== 0) {
    throw new Error(`Could not export ${service.file}: ${result.stderr || result.stdout}`);
  }
  writeFileSync(resolve(outputDir, service.file), `${result.stdout.trim()}\n`);
}

console.log(`OpenAPI contracts written to ${outputDir}`);
