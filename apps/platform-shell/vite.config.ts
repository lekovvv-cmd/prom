import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";
import { fileURLToPath, URL } from "node:url";

const rootDir = fileURLToPath(new URL(".", import.meta.url));
const indexHtml = fileURLToPath(new URL("index.html", import.meta.url));

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
    include: [
      "src/**/*.test.{ts,tsx}",
      "../../packages/frontend/api-client/src/**/*.test.{ts,tsx}",
      "../../packages/frontend/auth/src/**/*.test.{ts,tsx}",
      "../../packages/frontend/ui/src/**/*.test.{ts,tsx}",
      "../../packages/frontend/layout/src/**/*.test.{ts,tsx}",
      "../../packages/frontend/utils/src/**/*.test.{ts,tsx}",
      "../projects/frontend/**/*.test.{ts,tsx}",
      "../service-desk/frontend/**/*.test.{ts,tsx}",
    ],
    exclude: ["e2e/**", "node_modules/**", "dist/**"],
  },
  server: {
    port: 5173,
    fs: {
      allow: [
        rootDir,
        fileURLToPath(new URL("../projects/frontend", import.meta.url)),
        fileURLToPath(new URL("../service-desk/frontend", import.meta.url)),
        fileURLToPath(new URL("../../packages/frontend", import.meta.url)),
      ],
    },
  },
});
