# CLAUDE.md — frontend

SPA Vite + React 19 + TypeScript strict, React Router 8 (modo data), Ant Design 6, `@tanstack/react-query` con cliente generado por Orval 8. Proyecto npm aislado (no está en el workspace `uv`). Node 24 (`.nvmrc`).

## Archivos clave

- `openapi.json` — contrato versionado, exportado del backend. No editar ni formatear a mano (Biome lo excluye).
- `orval.config.ts` — genera `src/api/generated/` (ignorado por git) con el mutator `src/api/http.ts` (`customFetch`, `ApiError`, timeout 5 s).
- `src/pages/HealthPage.tsx` — página `/`; los `data-testid` (`health-loading`, `health-status`, `health-database`, `health-error`) son contrato de los tests unitarios y de `e2e`.
- `vite.config.ts` — `envDir: '..'` (lee el `.env` raíz), puerto `FRONTEND_DEV_PORT`, config de Vitest.
- `nginx.conf` + `Dockerfile` — producción: build estático con `VITE_API_BASE_URL=/api` y proxy `/api/` → backend.

## Comandos (desde `frontend/`)

```bash
npm ci --include=dev          # --include=dev por si NODE_ENV=production está en el shell
npm run dev                   # http://localhost:5173 (HMR); regenera el cliente Orval antes
npm run build                 # tsc -b && vite build; no necesita el backend en ejecución
npm run lint                  # biome lint + eslint (solo reglas react-hooks / react-refresh)
npm run format                # biome format --write
npm run format:check
npm run typecheck
npm test                      # vitest run (jsdom)
npm run generate:api          # regenerar el cliente a mano
```

Si cambia la API: desde la raíz `uv run python -m backend.export_openapi` y commitear `openapi.json`.
