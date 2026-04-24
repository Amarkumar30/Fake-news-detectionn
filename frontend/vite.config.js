import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const packageJson = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf-8"));

export default defineConfig({
  appType: "spa",
  plugins: [react()],
  esbuild: false,
  define: {
    __APP_VERSION__: JSON.stringify(packageJson.version),
  },
  server: {
    port: 3000,
    strictPort: true,
    host: "0.0.0.0",
  },
  preview: {
    port: 3000,
    strictPort: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
    pool: "threads",
    poolOptions: {
      threads: {
        singleThread: true,
        isolate: true,
      },
    },
  },
});
