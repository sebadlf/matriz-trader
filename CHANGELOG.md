# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [0.3.0] - 2026-11-24

### Added

- Variables de configuración de las librerías internas en el `.env` de la raíz: `PRIMARY_USER`, `PRIMARY_PASSWORD` y `PRIMARY_BASE_URL` (`matriz-client`), y `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE`, `MARKET_DATA_AUTH0_TOKEN_URL` y `MARKET_DATA_BASE_URL` (`market-data-client`). `.env.example` las documenta en dos secciones, con un comentario por variable y placeholders no secretos.
- `Settings` (`backend/app/core/config.py`) expone las ocho variables como campos tipados con los mismos nombres que leen las librerías: credenciales no vacías, secretos como `SecretStr` y URLs como `HttpUrl` (solo `http`/`https` absolutas). `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` tienen como default el de cada librería (reMarkets y market data develop).
- Al arrancar, el backend registra el log `external_endpoints` con los hosts efectivos de Primary, market data y Auth0, sin credenciales ni URLs completas, para que quede a la vista contra qué entorno opera.

### Changed

- Las seis credenciales son obligatorias: si falta alguna o está vacía (o solo tiene espacios), `python -m app` y `alembic` salen con código 1 y nombran cada variable en stderr. Un `.env` anterior a esta versión tiene que completarse a partir de `.env.example`.
- `load_settings()` imprime una línea `VARIABLE: mensaje` por error, sin el valor recibido, y corta el traceback encadenado, de modo que `PRIMARY_PASSWORD` y `MARKET_DATA_CLIENT_SECRET` nunca aparecen en stderr.
- Los tests del backend (`test_env` en `backend/tests/conftest.py`) y el job `migrations` de CI definen credenciales ficticias.

## [0.2.0] - 2026-11-23

### Added

- `scripts/gate.sh` como único punto de entrada de los gates (`backend`, `frontend`, `e2e`, `migrations`, `changed`, `branch` y `file`, en modo `quick` o `full`). Lo invocan CI, lefthook, los hooks de Claude Code, el hook de Octo y la ejecución manual. `scripts/verify-guards.sh` inyecta violaciones de prueba (`scripts/guard-probes/`) y falla si alguna herramienta deja de detectarlas.
- CI en GitHub Actions (`.github/workflows/ci.yml`) con los jobs `backend`, `frontend`, `e2e`, `migrations`, `security` y `workflow-lint`, más el agregador `ci-ok`. Usa filtros por rutas, caché de dependencias, `permissions: {}` y acciones fijadas por SHA. `market-libs` se instala con el secret `MARKET_LIBS_TOKEN`. El ruleset de `main` está en `.github/rulesets/main.json` y la plantilla de PR, en `.github/pull_request_template.md`.
- Hooks de git con lefthook (`lefthook.yml`): gate `quick` por módulo tocado, guard de `generated/` sin `openapi.json`, gitleaks sobre lo stageado y formato Conventional Commits del mensaje.
- Hooks de Claude Code (`.claude/settings.json`, `.claude/hooks/`): bloqueo de archivos generados y protegidos (`PreToolUse`), formato y lint del archivo editado (`PostToolUse`) y gate `full` de los módulos con cambios antes de terminar el turno (`Stop`).
- Backend: capas verificadas con import-linter (`app.scripts` → `app.main` → `app.api` → `app.services` → `app.db | app.schemas` → `app.domain` → `app.core`); errores RFC 9457 (`application/problem+json`, `ProblemDetails`) con `correlation_id`; logging estructurado con structlog y asgi-correlation-id (header `X-Request-ID`, redacción de secretos); `Clock` inyectable en UTC; tipos `Price`, `Quantity` y `Money` sobre `Decimal`, y Alembic con la plantilla async.
- Tests del backend: cobertura de branches ≥ 85 % (pytest-cov), orden aleatorio (pytest-randomly), propiedades con Hypothesis, contrato con Schemathesis sobre `openapi.json`, PostgreSQL 17 con testcontainers (`pytest -m db`) y tests de arquitectura que rechazan `float` en campos de precio, cantidad o monto.
- Frontend: reglas de dependencia entre carpetas con dependency-cruiser (`vp run lint:arch`), código sin usar con knip (`vp run lint:unused`), cobertura ≥ 70 % con `@vitest/coverage-v8`, MSW 2 con handlers generados por Orval, accesibilidad WCAG 2.2 AA con `@axe-core/playwright` y presupuesto de bundle (240 kB gzip) con size-limit.
- Frontend: `ApiError` (`status`, `title`, `detail`, `correlationId`) lanzado por el mutator ante `application/problem+json`, y formatters de precio y cantidad `es-AR` en `src/utils/format.ts`.
- Seguridad: gitleaks, `scripts/audit.py` (pip-audit y OSV-Scanner contra `security-allowlist.toml`, con motivo y vencimiento por entrada), actionlint, zizmor y Renovate (`renovate.json`, `minimumReleaseAge` de 7 días y seguimiento de los tags de `market-libs`).
- `backend/CLAUDE.md` y `frontend/CLAUDE.md` con las convenciones de cada módulo y las reglas obligatorias para la primera feature que envíe órdenes: `client_order_id` único, controles de riesgo, kill switch, auditoría de solo inserción, rate limiting y confirmación en la UI.

### Changed

- Ruff suma los grupos `ASYNC`, `FAST`, `S`, `DTZ`, `BLE`, `TRY`, `T20`, `ERA`, `PT`, `PIE`, `RET`, `C4`, `PTH`, `LOG`, `G`, `PERF`, `TC`, `ARG`, `FURB`, `TID`, `PL`, `C90` y `FBT`, y cada excepción tiene su justificación. `tests/test_tooling.py` falla si se quita alguno.
- Oxlint activa las categorías `correctness` y `suspicious` y prohíbe `any`, `!`, `console`, `enum`, `dangerouslySetInnerHTML`, `fetch` fuera del mutator e imports relativos que suben más de un nivel. TypeScript suma `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, `verbatimModuleSyntax` y otros flags estrictos.
- `CLAUDE.md` en la raíz queda reducido a contexto, comandos, Definición de terminado y checklist, y remite a los `CLAUDE.md` de cada módulo. Se completó el steering de Octo (`.octo/steering/`).
- Los colores primario, de link y de texto secundario del tema (`src/app/theme.ts`) se oscurecieron para cumplir el contraste WCAG AA.

### Fixed

- El hook de Octo `.octo/hooks/code-validate-improve.json` ya no corre `npm run typecheck`, un comando que no existía; ahora corre `scripts/gate.sh branch full`.

### Notas

- Los escenarios que dependen de GitHub (filtro por rutas, caché, secret ausente, ruleset aplicado y `ci-ok` en menos de 10 min) se verifican en el primer PR. Antes hay que crear el secret `MARKET_LIBS_TOKEN` y aplicar `.github/rulesets/main.json`.

## [0.1.0] - 2026-11-23

### Added

- Esqueleto del monorepo con los módulos `backend/` y `frontend/` y un único `.env` en la raíz (ignorado por git), documentado en `.env.example`.
- Backend en Python 3.13 con FastAPI, SQLAlchemy 2.0 async (PostgreSQL 17 + psycopg 3), pydantic-settings y uv, con `market-data-client` (`market-data-client-v0.7.1`) y `matriz-client` (`matriz-client-v0.4.0`) instaladas por SSH desde `gravity-quant/market-libs`.
- Endpoint `GET /api/health` y esquema OpenAPI versionado en `backend/openapi.json`, exportable con `uv run python -m app.scripts.export_openapi`.
- Validación de la configuración al arrancar: `python -m app` sale con código 1 y `Configuración inválida: <VARIABLE>` si falta una variable o es inválida.
- Calidad del backend: Ruff (con las reglas `ANN` sin excepciones), mypy `strict` con el plugin `pydantic.mypy` y pytest + pytest-asyncio + `httpx.AsyncClient`, incluido un test que detecta un `openapi.json` desactualizado.
- Frontend en React 19 + TypeScript `strict` sobre Vite+ (`vp`), con Ant Design 6, React Router 7, Zustand y TanStack Query, organizado en `app/`, `api/`, `screens/`, `components/`, `layouts/`, `hooks/`, `stores/`, `utils/`, `constants/`, `types/` y `test/`.
- Cliente de la API generado con Orval 8 (`vp run generate:api`, variante react-query) a partir de `backend/openapi.json`, con un único mutator `fetch` en `src/api/mutator.ts`.
- Pantalla de inicio que consulta `GET /api/health` y pantalla 404 para rutas desconocidas.
- Tests unitarios con `vp test` (Vitest + React Testing Library y el helper `renderWithProviders()`) y tests e2e con Playwright (`vp run e2e`), que mockean `/api/health` y no necesitan backend.
- Docker Compose en dos archivos independientes: `docker-compose.dev.yml` (recarga automática en backend y frontend) y `docker-compose.prod.yml` (imágenes sin herramientas de desarrollo y nginx que sirve el build y hace proxy de `/api`). Cada servicio se puede levantar por separado y PostgreSQL persiste en un volumen con nombre.
- `CLAUDE.md` con las convenciones, reglas de dependencia y comandos del proyecto, y `README.md` con la instalación y el uso.

### Notas

- Los `docker compose ... up --build` de ambos modos todavía no se verificaron de punta a punta (el daemon de Docker no pudo descargar imágenes en la máquina de verificación); `docker compose config` y el servicio `db` sí funcionan.
- `vp lint` y `vp check` muestran un warning conocido (`react/only-export-components` en `src/app/router.tsx`).
