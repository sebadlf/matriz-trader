---
inclusion: always
description: File organization and architectural patterns.
---

# Structure

- **Key directories**: dos módulos (`backend/`, `frontend/`) más la infraestructura de calidad en la raíz.
  - `backend/app/`: API FastAPI (`api/`, `services/`, `db/`, `schemas/`, `domain/`, `core/`, `scripts/`); `backend/migrations/` (Alembic); `backend/tests/`; `backend/openapi.json` (generado y versionado).
  - `frontend/src/`: `app/` (providers, router, tema), `api/` (mutator y `generated/` de Orval), `screens/`, `components/`, `layouts/`, `hooks/`, `stores/`, `utils/`, `constants/`, `types/`, `test/`; `frontend/e2e/` (Playwright).
  - `scripts/`: `gate.sh` (único punto de entrada de los gates), `verify-guards.sh` y `guard-probes/` (violaciones de prueba), `hooks/` (lefthook) y `audit.py`.
  - `.claude/` (hooks de Claude Code), `.octo/` (specs, steering y hooks de Octo), `.github/` (CI, ruleset de `main`, plantilla de PR), `lefthook.yml`, `renovate.json`, `security-allowlist.toml`.
- **Module boundaries**: capas verificadas por herramientas en cada módulo y un único contrato entre ellos.
  - Backend, capas de arriba hacia abajo: `app.scripts` → `app.main` → `app.api` → `app.services` → `app.db | app.schemas` → `app.domain` → `app.core`. Cada capa importa solo de las de abajo. `app.domain` no importa `fastapi`, `sqlalchemy`, `httpx` ni `matriz_client`. `app.api` no toca `app.db` ni `sqlalchemy`, salvo `app/api/deps.py` (`SessionDep`). Lo verifica `uv run lint-imports`.
  - Frontend: `app/` importa todo; `screens/` importa de `components`, `layouts`, `hooks`, `stores`, `api`, `utils`, `constants` y `types`; una pantalla nunca importa de otra; `components/` no importa de `screens/`, `api/`, `stores/` ni `layouts/`; `hooks/` no importa de `screens/`, `components/` ni `layouts/`; `utils/` y `constants/` solo de `types/`; sin ciclos; una pantalla se importa por su `index.ts`. Lo verifica `vp run lint:arch` (dependency-cruiser).
  - Entre módulos, el único contrato es `backend/openapi.json`: el frontend lo consume a través del cliente Orval generado; `fetch` solo existe en `src/api/mutator.ts`.
  - Un único `.env` en la raíz para backend, frontend y Docker Compose.
- **Where new code should go**: según la capa o carpeta que corresponda:
  - Endpoint nuevo: `backend/app/api/routes/<grupo>.py`, registrado en `app/api/router.py`, con esquemas en `app/schemas/` y la lógica en `app/services/`.
  - Regla o tipo de negocio puro (precios, ticks, validaciones de riesgo sin I/O): `backend/app/domain/`. Errores de negocio: subclases de `DomainError`.
  - Modelo ORM: `backend/app/db/` heredando de `Base`, con su migración en `backend/migrations/versions/`.
  - Infraestructura transversal (config, reloj, logging): `backend/app/core/`.
  - Pantalla nueva: `frontend/src/screens/<NombreScreen>/` con `index.ts`, su ruta en `src/app/routes.tsx` y el path en `src/constants/routes.ts`. Lo que comparten dos pantallas sube a `components/` o `hooks/`.
  - Funciones puras sin React: `frontend/src/utils/`. Estado global de cliente: `frontend/src/stores/`.
  - Un gate o chequeo nuevo: dentro de `scripts/gate.sh`, nunca repetido en CI, lefthook ni hooks.
