import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, lazyPlugins, loadEnv } from "vite-plus";

// Único .env del monorepo: vive en la raíz del repositorio (AC-3).
const ROOT_ENV_DIR = fileURLToPath(new URL("..", import.meta.url));

// Única fuente de configuración de Vite, Oxlint, Oxfmt y Vitest (NFR-4).
export default defineConfig(({ mode }) => {
  // Lee <repo>/.env y process.env; sin prefijo VITE_ no llega al bundle.
  const env = loadEnv(mode, ROOT_ENV_DIR, "");

  return {
    envDir: ROOT_ENV_DIR,
    plugins: lazyPlugins(() => [react()]),
    resolve: {
      alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target: env.BACKEND_URL ?? "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    lint: {
      plugins: ["react", "typescript", "oxc"],
      ignorePatterns: ["src/api/generated/**", "dist/**"],
      rules: {
        "react/rules-of-hooks": "error",
        "react/only-export-components": ["warn", { allowConstantExport: true }],
        "vite-plus/prefer-vite-plus-imports": "error",
      },
      options: { typeAware: true, typeCheck: true },
      jsPlugins: [{ name: "vite-plus", specifier: "vite-plus/oxlint-plugin" }],
    },
    fmt: {
      ignorePatterns: ["src/api/generated/**", "dist/**", "pnpm-lock.yaml"],
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      css: false,
    },
  };
});
