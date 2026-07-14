import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDirectory = dirname(dirname(fileURLToPath(import.meta.url)));
const repositoryDirectory = resolve(frontendDirectory, "..");
const isWindows = process.platform === "win32";
const playwrightExecutable = isWindows ? "playwright.cmd" : "playwright";
const composeArguments = [
  "compose",
  "--project-name", "prom-e2e",
  "--file", "docker-compose.yml",
  "--file", "docker-compose.e2e.yml"
];

function run(command, args, options = {}) {
  return new Promise((resolveRun, rejectRun) => {
    const child = spawn(command, args, {
      cwd: repositoryDirectory,
      env: process.env,
      stdio: "inherit",
      shell: isWindows,
      ...options
    });
    child.on("error", rejectRun);
    child.on("exit", (code, signal) => {
      if (code === 0) resolveRun();
      else rejectRun(new Error(`${command} ${args.join(" ")} завершилась с кодом ${code ?? signal}.`));
    });
  });
}

try {
  await run("docker", [...composeArguments, "up", "--build", "--detach", "--wait"]);
  await run(
    resolve(frontendDirectory, "node_modules", ".bin", playwrightExecutable),
    ["test", ...process.argv.slice(2)],
    {
      cwd: frontendDirectory,
      env: {
        ...process.env,
        E2E_BASE_URL: "http://127.0.0.1:5174",
        E2E_SERVICE_DESK_URL: "http://127.0.0.1:8002"
      }
    }
  );
} finally {
  await run("docker", [...composeArguments, "down", "--volumes", "--remove-orphans"])
    .catch((error) => console.error(`Не удалось убрать временный E2E-стенд: ${error.message}`));
}
