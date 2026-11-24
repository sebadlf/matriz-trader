🔧 **Read** `guardas-de-calidad-y-buenas-practicas/requirements.md`🔧 **Read** `guardas-de-calidad-y-buenas-practicas/plan.md`1	# Requirements: Guardas de calidad y buenas prácticas (backend, frontend y agentes)
2	
3	## Introduction
4	
5	`matriz-trader` va a ser un cliente de trading **manual asistido y algorítmico** sobre Matriz, construido con `market-data-client` y `matriz-client`. Hoy es un esqueleto (solo `GET /api/health`) y la mayor parte del código nuevo la van a escribir **agentes de IA** (Claude Code y Octo), con personas revisando. Los agentes cumplen lo que se verifica de forma automática, pero no siempre lo que solo está escrito. Este spec convierte las buenas prácticas en **gates ejecutables** antes de 
… (truncated)1	# Plan: Guardas de calidad y buenas prácticas (backend, frontend y agentes)
2	
3	> Convertir las convenciones de `CLAUDE.md` y las prácticas de FastAPI, React y del dominio trading en gates bloqueantes que corren con un mismo script (`scripts/gate.sh`) en cuatro lugares: cuando el agente edita o termina un turno, en el commit, en el hook de Octo y en CI. Appetite: L. Risk: medium.
4	
5	## Approach
6	
7	```mermaid
8	flowchart LR
9	  A["Spike: Oxlint, uv audit, TS flags, Renovate"] --> B["Config de herramientas por módulo"]
10	  B --> C["Código base: dominio, Clock, errores RFC 9457, logging, 
… (truncated)🔧 **Bash**

```bash
git diff --stat && git diff .gitignore frontend/pnpm-workspace.yaml frontend/orval.config.ts backend/tests/conftest.py frontend/src/app/theme.ts frontend/src/api/mutator.ts | head -250
``` .gitignore                                         |   10 +
 .octo/hooks/code-validate-improve.json             |    4 +-
 .octo/steering/product.md                          |   17 +-
 .octo/steering/structure.md                        |   23 +-
 .octo/steering/tech.md                             |   25 +-
 CLAUDE.md                                          |  313 +---
 README.md                                          |  117 +-
 backend/app/__main__.py                            |    5 +
 backend/app/api/router.py                          |    3 +-
 backend/app/api/routes/health.py         
… (truncated)🔧 **Bash**

```bash
git diff frontend/package.json frontend/vite.config.ts README.md | grep '^[+-]' | head -150; echo ----; head -30 frontend/src/app/providers.test.tsx; echo ----; head -30 backend/tests/test_deps.py; echo ---; grep -n "def test" backend/tests/test_migrations.py backend/tests/test_contract.py backend/tests/test_errors.py backend/tests/test_logging.py; cat backend/.squawk.toml; head -40 scripts/verify-guards.sh
```--- a/README.md
+++ b/README.md
-Las convenciones de código, la estructura de carpetas y el flujo de regeneración del cliente Orval están en [`CLAUDE.md`](CLAUDE.md).
+Las convenciones de código están en [`CLAUDE.md`](CLAUDE.md) (contexto, gates, Definición de terminado y checklist), [`backend/CLAUDE.md`](backend/CLAUDE.md) y [`frontend/CLAUDE.md`](frontend/CLAUDE.md) (estructura, reglas de dependencia y flujo de regeneración del cliente Orval).
-| Docker + Docker Compose | Compose ≥ 2.24 | Modo contenedores (dev y prod) |
+| Docker + Docker Compose | Compose ≥ 2.24 | Modo contenedores (dev y 
… (truncated)## Resumen

Se convirtieron las convenciones de `CLAUDE.md` en gates ejecutables y bloqueantes. Un único script, `scripts/gate.sh`, corre los mismos chequeos cuando el agente edita o termina un turno, en cada commit, en el hook de Octo y en CI. Con esto el repo queda listo para que lo desarrollen agentes de IA sin que una violación de arquitectura, tipos, seguridad o dominio llegue a `main`.

## Cambios

- **Gates y CI**:
  - `scripts/gate.sh` define cada gate una sola vez: `backend`, `frontend`, `e2e`, `migrations`, `changed`, `branch` y `file`, en modo `quick` o `full`.
  - `verify-guards.sh` y `guard-probes/` inyectan violaciones de prueba y exigen que cada herramienta las rechace con la regla esperada.
  - `ci.yml` tiene filtros de rutas por job, acciones fijadas por SHA, `permissions: {}` y el agregador `ci-ok`.
  - El ruleset de `main` se aplica con `gh api`. Renovate queda configurado.
  - La auditoría de dependencias usa pip-audit y OSV-Scanner, con una allowlist donde cada entrada vence.
- **Hooks**:
  - lefthook corre en el commit: gate `quick`, guard de `generated/` sin `openapi.json`, gitleaks y Conventional Commits.
  - Claude Code tiene tres hooks: `PreToolUse` bloquea archivos generados o protegidos, `PostToolUse` formatea y lintea cada archivo editado, y `Stop` corre el gate `full`.
  - El hook de Octo ahora usa `scripts/gate.sh branch full` en lugar de `npm run typecheck`, que no existe en el repo.
- **Backend**:
  - Errores en formato RFC 9457 (`ProblemDetails`, `DomainError`).
  - Logging estructurado con structlog, `correlation_id` y ocultamiento de secretos, más un middleware de log de acceso.
  - Alembic con plantilla async y Squawk para el lint de migraciones.
  - Tests nuevos de contrato (Schemathesis), de migraciones contra PostgreSQL 17 (testcontainers), de errores, de logging y de dependencias.
- **Frontend**:
  - Más reglas de Oxlint en `vite.config.ts`, cobertura con umbrales y dependency-cruiser para las reglas entre carpetas.
  - knip para código sin usar, size-limit para el tamaño del bundle y MSW con handlers generados por Orval.
  - `ApiError` ahora expone `title`, `detail` y `correlationId`.
  - Formatters `es-AR` en `utils/format.ts`.
  - Test de accesibilidad con axe y un tema de AntD con contraste suficiente para WCAG AA.
- **Documentación**: `CLAUDE.md` raíz reducido y dividido en `backend/CLAUDE.md` y `frontend/CLAUDE.md`, que incluyen las reglas obligatorias para enviar órdenes. Steering de Octo completo, README actualizado y plantilla de PR.

## Archivos

**Repo, CI y hooks de git**
- `scripts/gate.sh`: punto de entrada único de todos los gates.
- `scripts/verify-guards.sh`: copia cada probe al módulo, exige que la herramienta falle con la regla esperada y después lo borra.
- `scripts/hooks/check-generated-sync.sh`: aborta el commit si cambia `frontend/src/api/generated/` sin `backend/openapi.json`.
- `scripts/hooks/commit-msg.sh`: valida Conventional Commits con primera línea de hasta 72 caracteres.
- `scripts/hooks/gitleaks-staged.sh`: corre gitleaks sobre lo stageado y falla si el binario no está instalado.
- `scripts/audit.py`: corre pip-audit y OSV-Scanner, filtra con la allowlist y falla si hay hallazgos o entradas vencidas.
- `security-allowlist.toml`: allowlist de vulnerabilidades, cada una con motivo y fecha de vencimiento.
- `lefthook.yml`: hooks `pre-commit` y `commit-msg`, que delegan en `gate.sh` y `scripts/hooks/`.
- `renovate.json`: agrupa las actualizaciones por módulo, espera 7 días antes de proponerlas y sigue los tags de `market-libs`.
- `.github/workflows/ci.yml`: jobs `changes`, `backend`, `frontend`, `e2e`, `migrations`, `security`, `workflow-lint` y `ci-ok`.
- `.github/rulesets/main.json`: protección de `main` (PR obligatorio, `ci-ok` requerido, rama actualizada, sin force-push ni borrado).
- `.github/pull_request_template.md`: plantilla de PR con link al spec, checklist, contrato de la API, capturas y sección de riesgo y rollback.
- `.gitignore`: ignora los artefactos de cobertura y de Hypothesis y los `_probe*` temporales, pero versiona las fuentes de los probes.

**Probes de `verify-guards.sh`**
- `scripts/guard-probes/backend/utcnow/app/_probe.py`: usa `datetime.utcnow`, que debe disparar `DTZ003`.
- `scripts/guard-probes/backend/naive_now/app/_probe.py`: usa `datetime.now()` sin zona horaria, que debe disparar `DTZ005`.
- `scripts/guard-probes/backend/async_sleep/app/_probe.py`: llama a `time.sleep` dentro de `async def`, que debe disparar `ASYNC251`.
- `scripts/guard-probes/backend/requests_import/app/_probe.py`: importa `requests`, que debe disparar `TID251`.
- `scripts/guard-probes/backend/domain_imports_fastapi/app/domain/_probe.py`: el dominio importa FastAPI, lo que debe romper el contrato «Dominio puro».
- `scripts/guard-probes/backend/api_imports_db/app/api/routes/_probe.py`: la API importa `app.db`, lo que debe romper el contrato «API sin acceso directo a la DB».
- `scripts/guard-probes/frontend/raw-fetch/src/components/_probe.tsx`: usa `fetch` fuera del mutator.
- `scripts/guard-probes/frontend/axios/src/components/_probe.tsx`: importa `axios`.
- `scripts/guard-probes/frontend/enum/src/types/_probe.ts`: declara un `enum`.
- `scripts/guard-probes/frontend/deep-relative/src/screens/_probeA/_probe.tsx`: usa un import relativo `../../`.
- `scripts/guard-probes/frontend/screen-to-screen/src/screens/_probeA/index.ts`: una pantalla importa de otra.
- `scripts/guard-probes/frontend/component-to-api/src/components/_probe.tsx`: un componente importa de `api/`.
- `scripts/guard-probes/frontend/cycle/src/utils/_probeA.ts`: lado A de un ciclo de imports.
- `scripts/guard-probes/frontend/cycle/src/utils/_probeB.ts`: lado B del mismo ciclo.
- `scripts/guard-probes/frontend/hook-to-component/src/hooks/_probe.ts`: un hook importa un componente.
- `scripts/guard-probes/frontend/hook-to-component/src/components/_probeComp.tsx`: el componente que importa ese hook.
- `scripts/guard-probes/frontend/utils-to-api/src/utils/_probe.ts`: `utils/` importa de `api/`.
- `scripts/guard-probes/frontend/layout-to-screen-internal/src/layouts/_probe.tsx`: importa un archivo interno de una pantalla sin pasar por su `index.ts`.

**Capa de agentes**
- `.claude/settings.json`: registra los hooks `PreToolUse`, `PostToolUse` y `Stop`.
- `.claude/hooks/lib.sh`: helpers compartidos por los hooks (lectura del JSON de entrada y rutas).
- `.claude/hooks/guard-paths.sh`: bloquea con exit 2 la edición de archivos generados, `.env*` y lockfiles, e indica cómo regenerarlos.
- `.claude/hooks/fmt-lint-file.sh`: corre `scripts/gate.sh file` sobre cada archivo editado.
- `.claude/hooks/stop-gate.sh`: corre `scripts/gate.sh changed full` y respeta `stop_hook_active`.
- `.octo/hooks/code-validate-improve.json`: reemplaza `npm run typecheck` por `scripts/gate.sh branch full`.
- `.octo/steering/product.md`: propósito, usuarios, objetivos y no-objetivos del producto.
- `.octo/steering/tech.md`: stack, comandos de gate y convenciones.
- `.octo/steering/structure.md`: carpetas, límites entre capas y dónde va el código nuevo.

**Documentación**
- `CLAUDE.md`: reducido a contexto, comandos, gates, Definición de terminado y checklist; remite a los `CLAUDE.md` de cada módulo.
- `backend/CLAUDE.md`: capas, tipos de dominio, errores, logging, base de datos, tests y reglas obligatorias para órdenes.
- `frontend/CLAUDE.md`: estructura, Orval, estado, UI, MSW y reglas de UI para órdenes.
- `README.md`: suma prerrequisitos, gates, lefthook, hooks de agentes, CI, secret `MARKET_LIBS_TOKEN`, ruleset, auditoría y Renovate.
- `.octo/specs/guardas-de-calidad-y-buenas-practicas/plan.md`: ajustes del plan durante la implementación.
- `.octo/specs/guardas-de-calidad-y-buenas-practicas/tasks.md`: tareas marcadas como completas.

**Backend**
- `backend/app/api/errors.py`: handlers RFC 9457 para `HTTPException`, validación, `DomainError` y excepciones no manejadas, más `PROBLEM_RESPONSES`.
- `backend/app/domain/errors.py`: clase base `DomainError` para los errores de negocio.
- `backend/app/schemas/problem.py`: esquemas `ProblemDetails` y `ValidationIssue`.
- `backend/app/api/middleware.py`: log de acceso estructurado por request.
- `backend/app/core/logging.py`: `configure_logging` (JSON en producción, consola en desarrollo) y `redact_sensitive` para ocultar secretos.
- `backend/alembic.ini`: configuración de Alembic.
- `backend/migrations/env.py`: plantilla async con `Base.metadata` y la URL tomada de `Settings`.
- `backend/migrations/script.py.mako`: plantilla de las migraciones.
- `backend/.squawk.toml`: Squawk para PostgreSQL 17; excluye `prefer-text-field`, que dispara la tabla interna `alembic_version`.
- `backend/tests/conftest.py`: fixture que restaura el root logger y structlog después de cada test.
- `backend/tests/test_errors.py`: respuestas `problem+json` para 404, 405, 422, `DomainError` y 500, y su declaración en el OpenAPI.
- `backend/tests/test_logging.py`: `X-Request-ID`, log de acceso en JSON, ocultamiento de secretos y salida de consola.
- `backend/tests/test_contract.py`: Schemathesis contra la app ASGI.
- `backend/tests/test_migrations.py`: test marcado `db` que corre `upgrade head` sin drift contra PostgreSQL 17 con testcontainers.
- `backend/tests/test_deps.py`: verifica que `SessionDep` abre una sesión por request y el ciclo de vida de la app.

**Frontend**
- `frontend/vite.config.ts`: reglas de Oxlint ampliadas (imports y globales prohibidos) y cobertura v8 con umbrales.
- `frontend/package.json`: scripts `lint:arch`, `lint:unused`, `size` y `typecheck:node`, dependencias de calidad y MSW, y presupuesto de size-limit (240 kB gzip).
- `frontend/pnpm-workspace.yaml`: no ejecuta los postinstall de `msw` ni de `@swc/core`, con comentarios que lo justifican.
- `frontend/knip.config.ts`: configuración de knip, que excluye el código generado.
- `frontend/.dependency-cruiser.cjs`: reglas de dependencia entre carpetas y de ciclos.
- `frontend/orval.config.ts`: `mock: true` para generar los handlers de MSW.
- `frontend/src/api/mutator.ts`: `ApiError` expone `title`, `detail` y `correlationId` a partir de `ProblemDetails`.
- `frontend/src/api/mutator.test.ts`: tests de `ApiError` y del mutator.
- `frontend/src/app/theme.ts`: tokens de color con contraste suficiente para WCAG AA, que verifica axe.
- `frontend/src/app/providers.test.tsx`: verifica el `QueryClient` que crea `AppProviders` cuando no recibe uno.
- `frontend/src/utils/format.ts`: formatters de precio y cantidad con `Intl.NumberFormat` en `es-AR`.
- `frontend/src/utils/format.test.ts`: tests de los formatters.
- `frontend/e2e/a11y.spec.ts`: análisis con axe (WCAG 2.2 AA) de Home y de la 404.