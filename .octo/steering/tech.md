---
inclusion: always
description: Tech stack, frameworks, and engineering conventions.
---

# Tech

El detalle de cada regla está en `CLAUDE.md` (raíz), `backend/CLAUDE.md` y `frontend/CLAUDE.md`.

- **Languages / frameworks**: Python en el backend y TypeScript en el frontend.
  - Backend: Python 3.13, uv, FastAPI + uvicorn, pydantic-settings, PostgreSQL 17 + SQLAlchemy 2.0 async + psycopg 3, Alembic, structlog + asgi-correlation-id. Librerías internas `market-data-client` y `matriz-client` por SSH.
  - Frontend: TypeScript `strict`, React 19, Ant Design 6, Vite+ (`vp`), pnpm, Orval 8 (react-query), React Router 7, Zustand.
  - Calidad: Ruff, mypy `strict`, import-linter, pytest (cobertura, orden aleatorio, Hypothesis, Schemathesis, testcontainers), Squawk; Oxlint/Oxfmt vía `vp`, dependency-cruiser, knip, Vitest + MSW 2, Playwright + axe, size-limit; lefthook, gitleaks, actionlint, zizmor, pip-audit, OSV-Scanner y Renovate.
- **Build / test / lint commands**: `scripts/gate.sh` es el único punto de entrada; lo invocan CI, lefthook, los hooks de Claude Code y el hook de Octo.
  - `scripts/gate.sh backend [quick|full]` y `scripts/gate.sh frontend [quick|full]`: gate de cada módulo (`quick` en el commit, `full` en el agente y en CI).
  - `scripts/gate.sh e2e`: Playwright con accesibilidad (axe, WCAG 2.2 AA).
  - `scripts/gate.sh migrations`: `alembic upgrade head` + `alembic check` contra PostgreSQL 17 (Docker) y Squawk sobre el SQL.
  - `scripts/gate.sh changed full` (hook Stop) y `scripts/gate.sh branch full` (hook de Octo): gate de los módulos con cambios.
  - Definición de terminado: `scripts/gate.sh changed full`, más `e2e` si cambió la UI y `migrations` si cambiaron los modelos.
  - `python3 scripts/audit.py`: vulnerabilidades de dependencias contra `security-allowlist.toml`.
- **Conventions**: las que verifican los gates, más las de revisión:
  - Naming: rutas con `operation_id` en camelCase (`getHealth`) y `tags`; componentes en `PascalCase`, un componente por archivo; hooks `useAlgo` en `useAlgo.ts`; tests `test_<tema>.py` en el backend y `Algo.test.tsx` al lado del código en el frontend.
  - Error handling: el backend responde siempre `application/problem+json` (RFC 9457, `ProblemDetails`) con `correlation_id`; las reglas de negocio lanzan subclases de `DomainError`. El frontend recibe `ApiError` (`status`, `title`, `detail`, `correlationId`) desde el mutator y no traga errores.
  - State: datos del servidor en react-query vía Orval (nunca en Zustand); URL para filtros y selección; `Form` de AntD para formularios; Zustand solo para estado global de cliente.
  - Styling: tema de AntD en `src/app/theme.ts` vía `ConfigProvider`, sin colores ni espaciados hardcodeados; layout con componentes de AntD.
  - Números y tiempo: precios, cantidades y montos son `Decimal` en el backend y `string` en la API y el frontend; fechas con zona horaria en UTC vía el `Clock` inyectable.
  - Contrato: el frontend solo usa el cliente Orval generado desde `backend/openapi.json`; `openapi.json` y `src/api/generated/` se commitean juntos.
  - Commits: Conventional Commits (`<tipo>(<scope>)?: <descripción>`, hasta 72 caracteres).
  - Dependencias nuevas: solo OSS o gratuitas, sin duplicar una responsabilidad del stack y justificadas antes de instalarlas.
