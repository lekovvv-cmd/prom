import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { fileURLToPath, URL } from "node:url";

const rootDir = fileURLToPath(new URL(".", import.meta.url));
const indexHtml = fileURLToPath(new URL("index.html", import.meta.url));

export default defineConfig({
  root: rootDir,
  plugins: [react()],
  build: {
    rolldownOptions: {
      input: {
        main: indexHtml
      }
    }
  },
  test: {
    exclude: ["e2e/**", "node_modules/**", "dist/**"]
  },
  server: {
    port: 5173
  }
});
