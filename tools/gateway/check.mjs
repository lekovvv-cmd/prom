import { existsSync, readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const nginx = readFileSync(
  resolve(root, "apps/platform-shell/nginx.conf"),
  "utf8",
);
const compose = readFileSync(resolve(root, "compose.yaml"), "utf8");

const requiredNginxFragments = [
  "location /api/access/v1/",
  "location /api/access/v1/auth/mock/",
  "rewrite ^/api/access/v1/auth/mock/(.*)$ /auth/mock/$1 break;",
  "location /api/projects/v1/",
  "location /api/service-desk/v1/",
  "location = /healthz",
  "X-Request-ID $prom_request_id",
  "client_max_body_size",
  "proxy_connect_timeout",
  "X-Content-Type-Options",
  "resolver 127.0.0.11",
];

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
  requiredNginxFragments.push(`location ${registration.gatewayPrefix}`);
}

const missing = requiredNginxFragments.filter(
  (fragment) => !nginx.includes(fragment),
);
if (missing.length > 0) {
  throw new Error(`Gateway contract is missing: ${missing.join(", ")}`);
}

const exposedPorts = [...compose.matchAll(/^\s+ports:\s*\[(.+)\]\s*$/gm)].map(
  (match) => match[1],
);
if (exposedPorts.length !== 1 || !exposedPorts[0].includes("5173:80")) {
  throw new Error(
    `Only the shell gateway may expose a host port; found: ${exposedPorts.join(", ")}`,
  );
}

if (
  nginx.includes("location /api/ {") ||
  nginx.includes("location /service-desk-api/")
) {
  throw new Error("Legacy gateway aliases must not be exposed");
}

console.log("Gateway contract check passed.");
