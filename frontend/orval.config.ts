import { defineConfig } from "orval";

// Input: el OpenAPI versionado que exporta el backend (`uv run python -m app.scripts.export_openapi`).
// Output: código generado en `src/api/generated/` — no se edita a mano (NFR-6).
export default defineConfig({
  matrizTrader: {
    input: { target: "../backend/openapi.json" },
    output: {
      mode: "tags-split",
      client: "react-query",
      httpClient: "fetch",
      target: "src/api/generated",
      schemas: "src/api/generated/model",
      clean: true,
      override: {
        mutator: { path: "src/api/mutator.ts", name: "customFetch" },
      },
    },
  },
});
