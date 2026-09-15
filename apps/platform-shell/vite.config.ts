import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";
import { fileURLToPath, URL } from "node:url";

const rootDir = fileURLToPath(new URL(".", import.meta.url));
const indexHtml = fileURLToPath(new URL("index.html", import.meta.url));
const workspaceRoot = fileURLToPath(new URL("../..", import.meta.url));

export default defineConfig({
  root: rootDir,
  plugins: [react(), tailwindcss()],
  build: {
    rolldownOptions: {
      input: {
        main: indexHtml,
      },
    },
  },
  test: {
    // V8 must also transform untested files in sibling modules and packages.
    root: workspaceRoot,
    include: [
      "apps/platform-shell/src/**/*.test.{ts,tsx}",
      "packages/frontend/*/src/**/*.test.{ts,tsx}",
      "apps/*/frontend/**/*.test.{ts,tsx}",
    ],
    exclude: ["**/e2e/**", "**/node_modules/**", "**/dist/**"],
    coverage: {
      provider: "v8",
      reportsDirectory: "apps/platform-shell/coverage",
      include: [
        "apps/platform-shell/src/**/*.{ts,tsx}",
        "packages/frontend/*/src/**/*.{ts,tsx}",
        "apps/*/frontend/**/*.{ts,tsx}",
      ],
      exclude: ["**/*.test.{ts,tsx}", "**/*.d.ts"],
      reporter: ["text", "html", "lcov", "json-summary"],
      reportOnFailure: true,
      thresholds: { lines: 11, statements: 11, functions: 9, branches: 12 },
    },
  },
  server: {
    port: 5173,
    fs: {
      allow: [rootDir, workspaceRoot],
    },
  },
});
