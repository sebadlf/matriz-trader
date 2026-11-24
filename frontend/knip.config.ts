import type { KnipConfig } from "knip";

// Archivos, exports y dependencias sin usar. Lo ejecuta `vp run lint:unused` (AC-31).
// Cada excepción lleva su justificación: nunca se ignora código propio sin usar.
// src/main.tsx y src/test/setup.ts ya los detectan los plugins de Vite y Vitest de knip.
const config: KnipConfig = {
  entry: ["e2e/**/*.spec.ts"],
  project: ["src/**/*.{ts,tsx}", "e2e/**/*.ts"],
  ignore: ["src/api/generated/**"], // salida de Orval: no se edita a mano
  ignoreDependencies: [
    "@swc/core", // dependency-cruiser lo carga como parser (`options.parser: "swc"` en .dependency-cruiser.cjs)
    "zustand", // gestor de estado de cliente del stack (CLAUDE.md, stack); se quita al crear el primer store
  ],
};

export default config;
