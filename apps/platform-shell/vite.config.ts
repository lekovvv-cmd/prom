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
        main: indexHtml
      }
    }
  },
  test: {
    exclude: ["e2e/**", "node_modules/**", "dist/**"]
  },
  server: {
    port: 5173,
    fs: {
      allow: [rootDir, fileURLToPath(new URL("../projects/frontend", import.meta.url)), fileURLToPath(new URL("../service-desk/frontend", import.meta.url))]
    }
  }
});
