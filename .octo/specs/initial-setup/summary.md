🔧 **Read** `initial-setup/requirements.md`🔧 **Read** `initial-setup/plan.md`1	# Requirements — Initial setup (Matriz Trader)
2	
3	## Introduction
4	
5	Este ticket inicializa el proyecto **Matriz Trader** como un monorepo con cuatro partes: `frontend`, `backend`, `worker` y `model`, más la infraestructura compartida (PostgreSQL, configuración de entorno centralizada, Docker Compose, unit tests y tests de integración).
6	
7	El alcance es **solo la inicialización**: cada pieza debe existir, compilar/arrancar, pasar lint, formateo, type-check y tests, y comunicarse con las demás de punta a punta mediante un flujo mínimo de verificación ("health"). No se implementa funcion
… (truncated)1	# Plan — Initial setup (Matriz Trader)
2	
3	> Inicializar el monorepo `frontend` / `backend` / `worker` / `model` (+ `e2e`) con PostgreSQL, `.env` único, Docker Compose y tests, conectados de punta a punta por un flujo `GET /health`. **Appetite:** ~3–4 días de un desarrollador. **Riesgo:** medio (acceso y API de `matriz-client` sin verificar; Pyright strict sobre una librería posiblemente sin tipos).
4	
5	## Approach
6	
7	```mermaid
8	flowchart LR
9	    A["Raíz: .env único + uv workspace + VS Code/Claude"] --> B["model: DeclarativeBase + engine + Alembic"]
10	    B --> C["backend: FastAPI GE
… (truncated)🔧 **Bash**

```bash
cat frontend/src/router.tsx docker-compose.yml && ls frontend/src/pages && ls frontend && grep -c "\- \[x\]" .octo/specs/initial-setup/tasks.md; head -30 frontend/src/main.tsx; cat worker/src/worker/__main__.py | head -60
```import { createBrowserRouter } from 'react-router';
import { HealthPage } from './pages/HealthPage';

export const router = createBrowserRouter([{ path: '/', element: <HealthPage /> }]);
# Modo producción (AC-29..AC-33). `docker compose up postgres` levanta solo la base para dev.
name: matriz-trader

services:
  postgres:
    image: postgres:17-alpine
    env_file: .env
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      tim
… (truncated)## Overview

Este spec deja inicializado el monorepo de **Matriz Trader**: `frontend`, `backend`, `worker`, `model` y `e2e`, con PostgreSQL, un único `.env` en la raíz, Docker Compose y gates de calidad. Todas las piezas quedan conectadas de punta a punta por un flujo mínimo `GET /health`. No incluye funcionalidad de negocio; el objetivo es que cada pieza compile, arranque y pase lint, formato, tipos y tests.

## Changes

- **Raíz y tooling:** un único workspace `uv` (`model`, `backend`, `worker`, `e2e`) con un solo `uv.lock`, y Ruff y Pyright strict configurados solo en la raíz. Las versiones quedan fijadas en Python 3.13 y Node 24. Hay un `.env.example` con valores de ejemplo, y `.gitignore`/`.dockerignore` excluyen `.env` y `.env.*`. El workspace multi-root de VS Code usa Biome como formateador de TS/JS/JSON y Ruff para Python.
- **Model:** `Base(DeclarativeBase)` con naming convention, factories de engine y sesión para PostgreSQL (`psycopg`) y settings que leen el `.env` de la raíz. Alembic queda configurado para ejecución manual, con una migración `0001_initial` vacía.
- **Backend:** app FastAPI con `GET /health`. Responde 200 `{status: "ok", database: "ok"}` si la base es alcanzable, o 503 `{status: "degraded", database: "unavailable"}` en menos de 5 s si no lo es. CORS se configura desde `.env`. Si falta una variable obligatoria, sale con exit 2. El `app` se construye recién cuando se pide, así `export_openapi` y los tests funcionan sin `.env`. Un snapshot test falla si `frontend/openapi.json` quedó desactualizado.
- **Worker:** proceso async long-running que hace `login()` real contra `matriz-client` 0.3.0, instalado desde el wheel público de GitHub como fuente URL de `uv`. Corta ante SIGINT/SIGTERM con exit 0. Sale con 2 si faltan variables y con 1 si falla la conexión a Matriz. Todo el acoplamiento con la librería está en `MatrizClientGateway`.
- **Frontend:** Vite + React 19 + react-router + antd + react-query. Orval genera el cliente desde el `openapi.json` versionado, y el código generado no se versiona. `HealthPage` muestra tres estados: cargando, OK y error, este último en menos de 15 s. Biome se encarga del formato y el lint general; ESLint, con flat config, solo de `react-hooks` y `react-refresh`. Los tests corren con Vitest + Testing Library.
- **Docker / producción:** Compose levanta `postgres`, `backend`, `worker` y `frontend`. Los tres primeros tienen healthcheck, `depends_on: service_healthy` y un volumen nombrado `pgdata`. En el `frontend`, nginx sirve el build estático y hace proxy de `/api/` al backend.
- **Tests y gates:** unit tests en `model`, `backend`, `worker` y `frontend`, que no necesitan BD, Docker ni red. La suite e2e con Playwright (Python) lee `E2E_BASE_URL` del entorno o del `.env`. `scripts/check.sh` corre todos los gates y lista los que fallaron; `scripts/check-versions.sh` valida que las versiones de los Dockerfiles coincidan con `.python-version` y `.nvmrc`.
- **Documentación:** `README.md` y un `CLAUDE.md` por proyecto, con comandos verificados sobre un clon limpio (incluido `npm ci --include=dev`).

Dos cosas a tener en cuenta:

- **Worker con credenciales de ejemplo:** con las credenciales `changeme` del `.env.example`, el login a Matriz falla y el worker sale con 1. En Compose termina `exited` después de hasta 3 reinicios (`restart: on-failure:3`). Para que quede `running` sin reinicios hacen falta credenciales reales y Matriz accesible.
- **Archivos placeholder borrados:** `frontend/src/pages/HomePage.tsx` y `HomePage.test.tsx` eran placeholders temporales y se borraron cuando entró `HealthPage`. Por eso figuran en la lista de cambios aunque ya no existen.

## Files

- `.gitignore` — ignora `.env`/`.env.*` (excepto `.env.example`), venvs, `node_modules`, `dist`, el cliente generado y caches.
- `.dockerignore` — deja afuera de las imágenes `.env`, venvs, `node_modules`, `.git`, `.octo`, `.claude`, `.vscode` y caches.
- `.env.example` — todas las variables (Postgres, backend, frontend, `MATRIZ_*`, e2e) solo con valores de ejemplo; sin `MATRIZ_ACCOUNT` y con la URL de reMarkets.
- `.python-version` — fija Python 3.13.
- `.nvmrc` — fija Node 24.
- `pyproject.toml` — raíz del workspace `uv`, grupo `dev` (ruff, pyright, pytest, pytest-asyncio, httpx2), config de Ruff (excluye `frontend` y `.octo`) y Pyright strict.
- `matriz-trader.code-workspace` — workspace multi-root con Biome como formateador de TS/JS/JSON/JSONC y Ruff para Python.
- `.vscode/extensions.json` — recomienda las extensiones de Biome, Ruff y Python.
- `CLAUDE.md` — estructura del monorepo, convenciones y comandos desde la raíz.
- `README.md` — prerrequisitos, setup, dev por proyecto, Docker Compose, Alembic y tests.
- `docker-compose.yml` — servicios `postgres`, `backend`, `worker` y `frontend` con healthchecks, `depends_on` y volumen `pgdata`.
- `scripts/check.sh` — corre todos los gates de Python y frontend y resume los que fallaron.
- `scripts/check-versions.sh` — verifica que los `FROM` de Python/Node y `engines.node` coincidan con `.python-version`/`.nvmrc`.
- `model/pyproject.toml` — paquete `matriz-model` (SQLAlchemy 2, psycopg 3, pydantic-settings, alembic).
- `model/CLAUDE.md` — comandos y convenciones de `model`.
- `model/src/model/__init__.py` — API pública: `Base`, factories, `DatabaseSettings`, helpers de configuración.
- `model/src/model/base.py` — `Base(DeclarativeBase)` con naming convention.
- `model/src/model/db.py` — `create_engine_from_url` (timeouts cortos), `get_engine` (cacheado) y `get_sessionmaker`.
- `model/src/model/config.py` — `root_env_file()`, `DatabaseSettings` y `missing_env_vars()`.
- `model/alembic.ini` — config de Alembic con ejecución manual.
- `model/migrations/env.py` — usa `Base.metadata` y la URL de `DatabaseSettings`.
- `model/migrations/script.py.mako` — plantilla de revisiones.
- `model/migrations/versions/0001_initial.py` — migración inicial vacía.
- `model/tests/test_base.py` — tests de `Base`, del modelo tipado y del dialecto postgresql, sin conectarse.
- `backend/pyproject.toml` — paquete `matriz-backend` (fastapi, uvicorn, matriz-model).
- `backend/CLAUDE.md` — comandos del backend y regeneración de OpenAPI.
- `backend/Dockerfile` — imagen `python:3.13-slim` con uv y `uv sync --frozen` por capas.
- `backend/src/backend/settings.py` — `BackendSettings` y `load_settings()`; si falta una variable, loguea y sale con exit 2.
- `backend/src/backend/health.py` — `HealthResponse` y `GET /health` (200/503) con un probe de BD inyectable.
- `backend/src/backend/main.py` — `create_app()` con CORS opcional y `app` construido al pedirlo.
- `backend/src/backend/export_openapi.py` — escribe `frontend/openapi.json` sin levantar el servidor.
- `backend/tests/test_health.py` — 200, 503, `/openapi.json` y preflight CORS.
- `backend/tests/test_settings.py` — env faltante → `SystemExit(2)` con el mensaje esperado.
- `backend/tests/test_openapi_snapshot.py` — compara byte a byte el `openapi.json` versionado.
- `worker/pyproject.toml` — paquete `matriz-worker` con `matriz-client` desde URL, `httpx` y config de pytest-asyncio.
- `worker/CLAUDE.md` — comandos del worker y nota sobre `pyright` sin argumentos.
- `worker/Dockerfile` — imagen `python:3.13-slim` con `CMD` en forma exec (`python -m worker`).
- `worker/src/worker/settings.py` — `WorkerSettings` (`MATRIZ_BASE_URL`, `MATRIZ_USERNAME`, `MATRIZ_PASSWORD` como `SecretStr`, heartbeat, log level).
- `worker/src/worker/matriz_gateway.py` — protocolo `MatrizGateway`, `MatrizClientGateway` (`login`/`close`) y `GatewayError`.
- `worker/src/worker/runner.py` — loop con heartbeat, `run()` y `serve()` con manejo de SIGINT/SIGTERM.
- `worker/src/worker/__main__.py` — entrypoint: carga settings (exit 2 si falta algo), logging y `serve()`.
- `worker/tests/test_runner.py` — loop, parada, señales reales y log de inicialización con `FakeGateway`.
- `worker/tests/test_settings.py` — env faltante o inválido → exit 2 con log.
- `e2e/pyproject.toml` — paquete `matriz-e2e` (pytest, pytest-playwright).
- `e2e/CLAUDE.md` — cómo correr la suite contra el stack levantado.
- `e2e/tests/conftest.py` — fixture `base_url`: entorno, después `.env` raíz, después `http://localhost:8080`.
- `e2e/tests/test_health_page.py` — abre `/` en Chromium headless y verifica `status` y `database` = `ok`.
- `frontend/package.json` — dependencias y scripts (`generate:api` + pre-hooks, `build`, `lint`, `format:check`, `typecheck`, `test`).
- `frontend/CLAUDE.md` — comandos del frontend y reglas sobre Orval y `openapi.json`.
- `frontend/index.html` — HTML de entrada de Vite.
- `frontend/vite.config.ts` — `envDir: '..'`, puerto dev desde `.env` y Vitest con jsdom y `NODE_ENV=test`.
- `frontend/tsconfig.json` — referencias a los tsconfig de la app y de node.
- `frontend/tsconfig.app.json` — TypeScript strict para `src/`.
- `frontend/tsconfig.node.json` — config de TS para `vite.config.ts` y `orval.config.ts`.
- `frontend/biome.json` — formato y lint general; excluye el código generado y `openapi.json`.
- `frontend/eslint.config.js` — flat config solo con las reglas `react-hooks` y `react-refresh`.
- `frontend/orval.config.ts` — genera el cliente react-query desde `openapi.json` con el mutator `customFetch`.
- `frontend/src/api/http.ts` — `customFetch` con timeout de 5 s y `ApiError` para respuestas no-2xx.
- `frontend/src/queryClient.ts` — `QueryClient` con `retry: 1`, para que el error se vea en menos de 15 s.
- `frontend/src/main.tsx` — `ConfigProvider` + `QueryClientProvider` + `RouterProvider`.
- `frontend/src/router.tsx` — ruta `/` apuntando a `HealthPage`.
- `frontend/src/pages/HealthPage.tsx` — estados cargando, OK y error con componentes antd y `data-testid`.
- `frontend/src/pages/HealthPage.test.tsx` — tests de los tres estados con `fetch` mockeado.
- `frontend/src/pages/HomePage.tsx` — placeholder temporal de la primera etapa; se borró al reemplazarlo por `HealthPage`.
- `frontend/src/pages/HomePage.test.tsx` — test del placeholder, borrado junto con él.
- `frontend/src/test/setup.ts` — jest-dom y polyfill de `matchMedia` para antd.
- `frontend/src/vite-env.d.ts` — tipa `VITE_API_BASE_URL`.
- `frontend/Dockerfile` — build en `node:24-alpine` con `VITE_API_BASE_URL=/api` y runtime en `nginx:1.27-alpine`.
- `frontend/nginx.conf` — fallback de SPA, `/healthz` y proxy de `/api/` a `backend:8000`.
- `.octo/specs/initial-setup/requirements.md` — requisitos, criterios de aceptación y decisiones resueltas.
- `.octo/specs/initial-setup/plan.md` — plan de implementación y decisiones críticas tomadas en cada tarea.
- `.octo/specs/initial-setup/tasks.md` — las 14 tareas marcadas como completadas.
- `.octo/specs/initial-setup/matriz-client-notes.md` — análisis del wheel: es público, trae `py.typed`, la firma de `Client` y las variables finales `MATRIZ_*`.