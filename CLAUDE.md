# CLAUDE.md — matriz-trader

Guía para agentes de IA y desarrolladores que trabajan en este repo. Si una regla te impide resolver la tarea, detenete y explicá el conflicto antes de romperla. La instalación y el uso están en [`README.md`](README.md).

Este archivo tiene el contexto, los comandos, la Definición de terminado y la checklist. Las convenciones de cada módulo están en:

- [`backend/CLAUDE.md`](backend/CLAUDE.md): capas, tipos de dominio, errores, logging, base de datos, tests y reglas obligatorias para enviar órdenes.
- [`frontend/CLAUDE.md`](frontend/CLAUDE.md): estructura y reglas de dependencia, acceso al backend con Orval, estado, UI, tests y reglas de UI para órdenes.

Cuando una regla la hace cumplir una herramienta, la línea termina con «— lo verifica `<herramienta>`». Lo que no dice eso depende de la revisión.

## 1. Contexto

- `matriz-trader` va a ser un cliente de trading **manual asistido y algorítmico** sobre Matriz. Hoy es un esqueleto: el único endpoint es `GET /api/health` y el frontend tiene una pantalla de inicio y una 404. No hay lógica de negocio todavía.
- Monorepo con dos módulos: `backend/` (Python 3.13 + FastAPI) y `frontend/` (React + TypeScript + Vite+). Los comandos de cada módulo se ejecutan desde su carpeta; `scripts/gate.sh` se ejecuta desde cualquier lado.
- Las librerías internas `market-data-client` (tag `market-data-client-v0.7.1`) y `matriz-client` (tag `matriz-client-v0.4.0`) de `gravity-quant/market-libs` se instalan por SSH (`backend/pyproject.toml`, `[tool.uv.sources]`). En CI se instalan con el secret `MARKET_LIBS_TOKEN`.
- **Un único `.env`, en la raíz.** Lo leen el backend (`ROOT_ENV_FILE` en `backend/app/core/config.py`), el frontend (`envDir` en `frontend/vite.config.ts`) y Docker Compose. No crees `backend/.env` ni `frontend/.env` — lo verifica el hook `PreToolUse` (`.claude/hooks/guard-paths.sh`). Toda variable nueva se agrega a `.env.example` con un valor de ejemplo no secreto y un comentario.
- La mayor parte del código la escriben agentes. Por eso las convenciones se convierten en gates ejecutables que corren igual en el agente, en el commit y en CI (§4).

## 2. Stack

| Módulo | Herramientas |
|---|---|
| Backend | Python 3.13, uv, FastAPI + uvicorn, pydantic-settings, PostgreSQL 17 + SQLAlchemy 2.0 async + psycopg 3, Alembic, structlog + asgi-correlation-id |
| Calidad del backend | Ruff (con `ANN`), mypy `strict`, import-linter, pytest + pytest-asyncio + pytest-cov + pytest-randomly, Hypothesis, Schemathesis, testcontainers, Squawk |
| Frontend | TypeScript `strict`, React 19, Ant Design 6, Vite+ (`vp`), pnpm, Orval 8 (react-query), React Router 7, Zustand |
| Calidad del frontend | Oxlint y Oxfmt (vía `vp`), dependency-cruiser, knip, Vitest + `@vitest/coverage-v8` + React Testing Library + MSW 2, Playwright + `@axe-core/playwright`, size-limit |
| Repo | lefthook, gitleaks, GitHub Actions (actionlint, zizmor), pip-audit y OSV-Scanner (`scripts/audit.py`), Renovate |

No agregues librerías que dupliquen una responsabilidad de esta tabla (otro cliente HTTP, otro gestor de estado, otra librería de componentes, ESLint, Prettier, Jest, otro runner de hooks, etc.). Si necesitás una dependencia nueva, justificá por qué antes de instalarla. Todas las herramientas son OSS o gratuitas.

## 3. Comandos

`scripts/gate.sh` es el **único** lugar donde se define qué corre cada gate. CI, lefthook, los hooks de Claude Code, el hook de Octo y la ejecución manual lo invocan; ningún otro archivo repite la lista de comandos.

```bash
scripts/gate.sh backend [quick|full]      # gate del backend (default: full)
scripts/gate.sh frontend [quick|full]     # gate del frontend
scripts/gate.sh e2e                       # Playwright (incluye accesibilidad con axe)
scripts/gate.sh migrations                # Alembic contra PostgreSQL 17 (requiere Docker) + Squawk
scripts/gate.sh changed [quick|full]      # módulos con cambios sin commitear (lo usa el hook Stop)
scripts/gate.sh branch [quick|full]       # módulos que cambió la rama respecto de origin/main (hook de Octo)
scripts/gate.sh file <ruta>               # formatea y lintea un archivo (hook PostToolUse)
```

Sale con `0` si todo pasa, `1` si falla algún comando (con su salida sin filtrar) y `64` si los argumentos son inválidos. Si falta `uv`, `vp` o Docker, falla nombrando la herramienta: ningún gate se saltea en silencio.

| Gate | `quick` | `full` |
|---|---|---|
| `backend` | `ruff format`, `ruff check --fix`, `mypy`, `lint-imports` | `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest` (cobertura ≥ 85 %), `verify-guards.sh backend` |
| `frontend` | `vp check --fix`, `vp run lint:arch` | `vp check`, `vp run typecheck:node`, `lint:arch`, `lint:unused`, `vp test run --coverage` (≥ 70 %), `vp build`, `vp run size`, `verify-guards.sh frontend` |

`scripts/verify-guards.sh` inyecta violaciones de prueba (`scripts/guard-probes/`) y exige que cada herramienta las rechace con la regla esperada: así un gate que deja de detectar algo también falla.

Los comandos sueltos de cada módulo (servidor de desarrollo, regenerar el OpenAPI o el cliente Orval, etc.) están en `backend/CLAUDE.md` y `frontend/CLAUDE.md`.

## 4. Gates y dónde corren

| Momento | Qué corre | Dónde está definido |
|---|---|---|
| El agente edita un archivo | Bloquea archivos generados o protegidos (`frontend/src/api/generated/`, `backend/openapi.json`, `.env*`, `uv.lock`, `pnpm-lock.yaml`) e indica cómo regenerarlos | `.claude/hooks/guard-paths.sh` (`PreToolUse`) |
| El agente terminó de editar | `scripts/gate.sh file <ruta>`; los errores vuelven al agente | `.claude/hooks/fmt-lint-file.sh` (`PostToolUse`) |
| El agente intenta terminar el turno | `scripts/gate.sh changed full`; si falla, el turno no termina | `.claude/hooks/stop-gate.sh` (`Stop`) |
| Se completa una wave de Octo | `scripts/gate.sh branch full` | `.octo/hooks/code-validate-improve.json` |
| `git commit` | `scripts/gate.sh <módulo> quick` por módulo tocado, guard de `generated/` sin `openapi.json`, gitleaks, formato del mensaje | `lefthook.yml` y `scripts/hooks/` |
| PR contra `main` | Jobs `backend`, `frontend`, `e2e`, `migrations`, `security`, `workflow-lint` y el agregador `ci-ok` | `.github/workflows/ci.yml` |

- Los mensajes de commit siguen `<tipo>(<scope>)?: <descripción>`, con tipo en `feat|fix|chore|docs|refactor|test|perf|ci|build` y primera línea de hasta 72 caracteres — lo verifica `scripts/hooks/commit-msg.sh` (lefthook).
- No se commitean secretos — lo verifica gitleaks (lefthook y job `security`).
- `main` solo acepta PRs con el check `ci-ok` en verde y la rama actualizada, sin force-push — lo verifica el ruleset `.github/rulesets/main.json`.
- Las dependencias no tienen vulnerabilidades conocidas fuera de `security-allowlist.toml` (cada entrada con motivo y vencimiento) — lo verifica `scripts/audit.py` (job `security`).
- Los workflows declaran `permissions: {}`, permisos mínimos por job y acciones fijadas por SHA — lo verifican actionlint y zizmor (job `workflow-lint`).
- No uses `git commit --no-verify` para esquivar un gate: CI corre lo mismo en modo `full`.

## 5. Definición de "terminado"

Un cambio está terminado solo si pasa todo lo que corresponde y viste la salida de cada comando:

1. `scripts/gate.sh changed full` sale con `0` (corre el gate `full` de cada módulo con cambios sin commitear). Si ya commiteaste, usá `scripts/gate.sh branch full`.
2. `scripts/gate.sh e2e`, si el cambio toca un flujo cubierto por Playwright o la UI de una pantalla.
3. `scripts/gate.sh migrations`, si cambiaste modelos ORM o migraciones.
4. Si cambió el contrato de la API: `backend/openapi.json` y `frontend/src/api/generated/` regenerados y commiteados juntos (flujo en `frontend/CLAUDE.md`) — lo verifican `test_openapi_export.py` y el guard `scripts/hooks/check-generated-sync.sh`.

Si algún comando falla y no podés arreglarlo, informá exactamente qué falló, con la salida.

## 6. Checklist de autorrevisión

- [ ] ¿Toda llamada al backend usa código generado por Orval? ¿Edité algo en `src/api/generated/`?
- [ ] ¿Respeté las reglas de dependencia entre carpetas y capas? ¿Hay imports entre pantallas?
- [ ] ¿Cada estado está en el lugar correcto (servidor / URL / formulario / local / Zustand)?
- [ ] ¿Las pantallas manejan los estados de carga, error y vacío?
- [ ] ¿Hay `any`, `!`, `as` injustificados, `@ts-ignore` o `console.log`? ¿Hay funciones Python sin anotar?
- [ ] ¿Las rutas nuevas tienen `operation_id`, `tags` y un esquema de respuesta de `app/schemas/` (anotación de retorno)?
- [ ] ¿Los precios, cantidades y montos son `Decimal` en el backend y `string` en el frontend? ¿Las fechas tienen zona horaria?
- [ ] ¿Agregué variables de entorno? ¿Están en `.env.example` con comentario?
- [ ] ¿Agregué dependencias nuevas? ¿Están justificadas?
- [ ] ¿Pasó todo lo de la §5?
