# Matriz Trader

Monorepo con cinco proyectos y una suite de integración, conectados de punta a punta por `GET /health`:

| Directorio | Qué es | Stack |
|------------|--------|-------|
| `frontend/` | SPA: estado del backend y pantalla `/orders` (listar, crear y cancelar órdenes) | Vite, React, React Router, TypeScript, Orval (react-query), Ant Design, ESLint, Biome, Vitest |
| `backend/` | API HTTP (`GET /health`, `GET /accounts`, `GET /instruments`, `GET`/`POST /orders`, `POST /orders/cancel`, `GET /openapi.json`) | FastAPI, uvicorn |
| `worker/` | Proceso long-running que hace login en Matriz y conecta market data | asyncio, `market-data-client` |
| `broker/` | Único acceso a Matriz (`broker/src/broker/matriz_gateway.py`), compartido por `backend` y `worker` | `matriz-client` 0.3.0 |
| `model/` | Base de SQLAlchemy 2, engine/sesión y Alembic, compartidos por `backend` y `worker` | SQLAlchemy 2, psycopg 3, Alembic |
| `e2e/` | Tests de integración contra el sistema levantado | pytest, Playwright (Python) |

`model`, `broker`, `backend`, `worker` y `e2e` son miembros de un único workspace `uv` (un solo `uv.lock` en la raíz). `frontend` es un proyecto npm aislado (`frontend/package-lock.json`). Para VS Code, abrir `matriz-trader.code-workspace`.

## Prerrequisitos

- [uv](https://docs.astral.sh/uv/). Python 3.13 (`.python-version`) lo instala `uv` si hace falta.
- Node 24 (`.nvmrc`). Con nvm: `nvm use`.
- Docker con Docker Compose v2.

`matriz-client` se descarga del wheel público de GitHub Releases (`gravity-quant/market-libs`), declarado solo en `broker/pyproject.toml`; no hace falta token.

## Setup

Todos los comandos se ejecutan desde la raíz del repo salvo que se indique otra cosa.

```bash
cp .env.example .env                    # único .env del monorepo; completar MATRIZ_USERNAME / MATRIZ_PASSWORD / MATRIZ_ACCOUNTS
uv sync                                 # instala model, broker, backend, worker, e2e y las herramientas de dev
cd frontend && npm ci --include=dev && cd ..
```

- Todos los proyectos leen el `.env` de la raíz; no existen `.env` por proyecto. Una variable de entorno real gana sobre el `.env`.
- `POSTGRES_PASSWORD` tiene que ser URL-safe, porque se interpola en `DATABASE_URL`.
- `--include=dev` hace falta si el shell tiene `NODE_ENV=production`: sin eso `npm ci` omite las devDependencies (Vite, Biome, Orval…).

## Modo dev (cada proyecto por separado)

```bash
docker compose up postgres                                     # solo PostgreSQL, publicado en ${POSTGRES_PORT}
uv run alembic -c model/alembic.ini upgrade head               # migraciones (paso manual)
uv run uvicorn backend.main:app --reload --port 8000           # backend con recarga → http://localhost:8000/health
uv run python -m worker                                        # worker (Ctrl+C para detenerlo)
cd frontend && npm run dev                                     # frontend con HMR → http://localhost:5173
```

- El backend necesita `DATABASE_URL`; sin ella sale con código 2 y nombra la variable faltante. CORS acepta los orígenes de `CORS_ORIGINS` (métodos `GET` y `POST`).
- Las `MATRIZ_*` son opcionales en el backend: sin `MATRIZ_USERNAME`/`MATRIZ_PASSWORD`, `/health` responde igual y los endpoints de órdenes devuelven 503. El login es diferido (primer request). Las cuentas del selector salen de `MATRIZ_ACCOUNTS` (separadas por coma).
- El worker se conecta de verdad a Matriz al arrancar (`MATRIZ_BASE_URL`, `MATRIZ_USERNAME`, `MATRIZ_PASSWORD`). Si faltan variables sale con código 2; si el login falla (por ejemplo con las credenciales `changeme` del ejemplo) sale con código 1.
- El frontend llama a `VITE_API_BASE_URL` y regenera el cliente Orval desde `frontend/openapi.json` antes de `dev`, `build`, `typecheck` y `test`.

Si cambia la API del backend, regenerar y commitear el contrato:

```bash
uv run python -m backend.export_openapi                        # escribe frontend/openapi.json
```

`backend/tests/test_openapi_snapshot.py` falla si el archivo quedó desactualizado.

## Modo producción (Docker Compose)

```bash
docker compose up --build        # postgres, backend, worker y frontend (nginx) → http://localhost:${FRONTEND_PORT:-8080}
docker compose ps                # postgres/backend/frontend "healthy"
docker compose down              # conserva los datos (volumen pgdata); `down -v` los borra
```

nginx sirve el build estático del frontend y hace proxy de `/api/` al backend, así que en producción no hay CORS. `backend` y `worker` esperan al healthcheck de `postgres`. El worker tiene `restart: on-failure:3`: sin credenciales válidas de Matriz termina en `exited`, y `docker compose logs worker` muestra el motivo. Las migraciones no se ejecutan automáticamente.

## Tests y calidad

```bash
scripts/check.sh                 # todos los gates: versiones, ruff, pyright, pytest (model/broker/backend/worker) y lint/format/typecheck/test del frontend
```

Gates individuales:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright                                  # strict; correrlo sin argumentos (toma el include del pyproject)
cd model && uv run pytest                       # ídem en broker/, backend/ y worker/
scripts/check-versions.sh                       # .python-version/.nvmrc vs Dockerfiles y engines.node
cd frontend && npm run lint && npm run format:check && npm run typecheck && npm test
```

Los unit tests no necesitan PostgreSQL, Docker ni acceso a Matriz.

Tests de integración (requieren el stack levantado con `docker compose up --build`):

```bash
uv run playwright install chromium              # una sola vez
uv run pytest e2e
```

La URL del frontend sale de `E2E_BASE_URL` (entorno, luego `.env`, luego `http://localhost:8080`).
