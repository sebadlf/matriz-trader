import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, lazyPlugins, loadEnv } from "vite-plus";

// Patrones de import prohibidos en todo `src/`. Un override que redefina `no-restricted-imports`
// reemplaza estas opciones (no las combina): debe repetir la lista completa.
const RESTRICTED_IMPORTS = [
  {
    group: ["../../*", "../../**"],
    message: "Usá el alias @/ (frontend/CLAUDE.md, reglas de dependencia).",
  },
  {
    group: ["axios"],
    message:
      "El backend se consume solo vía el cliente Orval (frontend/CLAUDE.md, acceso al backend).",
  },
];

const FETCH_MESSAGE = "fetch solo en src/api/mutator.ts; usá el cliente Orval.";

// Único .env del monorepo: vive en la raíz del repositorio (AC-3).
const ROOT_ENV_DIR = fileURLToPath(new URL("..", import.meta.url));

// Única fuente de configuración de Vite, Oxlint, Oxfmt y Vitest (NFR-4).
export default defineConfig(({ mode }) => {
  // Lee <repo>/.env y process.env; sin prefijo VITE_ no llega al bundle.
  const env = loadEnv(mode, ROOT_ENV_DIR, "");

  return {
    envDir: ROOT_ENV_DIR,
    // `lazyPlugins` devuelve `PluginOption[] | undefined`; con `exactOptionalPropertyTypes` no se
    // puede asignar `undefined` a `plugins`.
    plugins: lazyPlugins(() => [react()]) ?? [],
    resolve: {
      alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target: env["BACKEND_URL"] ?? "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    lint: {
      plugins: ["react", "typescript", "oxc", "jsx-a11y", "import", "vitest", "promise", "unicorn"],
      // Sin `warn`: un warning no corta `vp check` y los gates son bloqueantes.
      categories: { correctness: "error", suspicious: "error", perf: "error" },
      ignorePatterns: ["src/api/generated/**", "dist/**", "coverage/**"],
      rules: {
        "react/rules-of-hooks": "error",
        "react/exhaustive-deps": "error",
        "react/only-export-components": ["error", { allowConstantExport: true }],
        "react/no-danger": "error",
        // Con `jsx: "react-jsx"` (tsconfig.json) no hace falta importar React en scope.
        "react/react-in-jsx-scope": "off",
        "typescript/no-explicit-any": "error",
        "typescript/no-non-null-assertion": "error",
        "typescript/no-floating-promises": "error",
        "typescript/ban-ts-comment": ["error", { "ts-expect-error": "allow-with-description" }],
        "no-console": "error",
        "import/no-cycle": "error",
        "no-restricted-globals": ["error", { name: "fetch", message: FETCH_MESSAGE }],
        "no-restricted-properties": [
          "error",
          { object: "window", property: "fetch", message: FETCH_MESSAGE },
          { object: "globalThis", property: "fetch", message: FETCH_MESSAGE },
        ],
        "no-restricted-imports": ["error", { patterns: RESTRICTED_IMPORTS }],
        "vite-plus/prefer-vite-plus-imports": "error",
      },
      overrides: [
        // Única excepción (frontend/CLAUDE.md §4): el mutator es el punto de fetch.
        {
          files: ["src/api/mutator.ts"],
          rules: { "no-restricted-globals": "off", "no-restricted-properties": "off" },
        },
        // El setup de tests registra matchers y efectos globales con imports sin binding.
        { files: ["src/test/setup.ts"], rules: { "import/no-unassigned-import": "off" } },
      ],
      options: { typeAware: true, typeCheck: true },
      jsPlugins: [{ name: "vite-plus", specifier: "vite-plus/oxlint-plugin" }],
    },
    fmt: {
      ignorePatterns: ["src/api/generated/**", "dist/**", "coverage/**", "pnpm-lock.yaml"],
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      css: false,
      // Ant Design en jsdom con cobertura v8 es lento en los runners de CI: 5 s (default) no alcanza.
      testTimeout: 15_000,
      coverage: {
        provider: "v8",
        include: ["src/**/*.{ts,tsx}"],
        // Definir `exclude` reemplaza los defaults de Vitest: los archivos de test se excluyen a mano.
        exclude: [
          "src/api/generated/**",
          "src/test/**",
          "e2e/**",
          "src/**/*.test.{ts,tsx}",
          "src/main.tsx",
          "src/vite-env.d.ts",
        ],
        thresholds: { lines: 70, branches: 70, functions: 70, statements: 70 },
      },
    },
  };
});
