# Plan — Initial setup (Matriz Trader)

> Inicializar el monorepo `frontend` / `backend` / `worker` / `model` (+ `e2e`) con PostgreSQL, `.env` único, Docker Compose y tests, conectados de punta a punta por un flujo `GET /health`. **Appetite:** ~3–4 días de un desarrollador. **Riesgo:** medio (acceso y API de `matriz-client` sin verificar; Pyright strict sobre una librería posiblemente sin tipos).

## Approach

```mermaid
flowchart LR
    A["Raíz: .env único + uv workspace + VS Code/Claude"] --> B["model: DeclarativeBase + engine + Alembic"]
    B --> C["backend: FastAPI GET /health"]
    B --> D["worker: proceso long-running + matriz-client"]
    C --> E["frontend: openapi.json → Orval → página /"]
    E --> F["docker compose: postgres + backend + worker + nginx"]
    F --> G["e2e: Playwright verifica la página raíz"]
```

Se construye de abajo hacia arriba sobre un único workspace `uv` en la raíz (miembros `model`, `backend`, `worker`, `e2e`) y un proyecto npm aislado en `frontend/`. Todo el código Python comparte un único `uv.lock`, una config de Ruff y una de Pyright strict en el `pyproject.toml` raíz. El contrato entre backend y frontend es un `frontend/openapi.json` versionado, exportado desde la app FastAPI sin levantarla, del que Orval genera el cliente react-query en cada `dev`/`build`/`test` (Resolved Decision). En producción, nginx sirve el build estático y hace proxy de `/api/*` al backend: un solo origen y sin CORS. En dev, el frontend llama directo al backend con CORS configurado desde `.env`. Alternativas descartadas: versionar el código generado por Orval, porque la decisión resuelta más reciente prefiere versionar `openapi.json`; servir el frontend desde FastAPI con `StaticFiles`, porque contradice el servicio `frontend` de AC-30; un proyecto `e2e` fuera del workspace, porque rompe el lockfile único de AC-22; y un `pyproject` independiente por proyecto Python, porque no daría un `uv.lock` único.

## Affected files

El workspace hoy contiene solo `.octo/specs/initial-setup/{requirements.md,plan.md,spec.json}` y los directorios vacíos `.claude/agents/` y `.claude/skills/*`. **Todos los archivos de abajo son nuevos**; la referencia `:1` indica creación.

| File | Change |
|------|--------|
| `.gitignore:1` | Nuevo: ignora `.env`, `.venv/`, `node_modules/`, `dist/`, `frontend/src/api/generated/`, `__pycache__/`, `.pytest_cache/`, `test-results/` (AC-27) |
| `.env.example:1` | Nuevo: todas las variables, solo con valores de ejemplo (AC-25, AC-44) |
| `.python-version:1` | Nuevo: `3.13` (AC-40) |
| `.nvmrc:1` | Nuevo: `24` (AC-40) |
| `.dockerignore:1` | Nuevo: excluye `.env`, `.venv`, `node_modules`, `dist`, `.git`, `.octo` (AC-44) |
| `pyproject.toml:1` | Nuevo: raíz del workspace `uv` + `[tool.ruff]` + `[tool.pyright]` (AC-22, AC-23, AC-24) |
| `uv.lock:1` | Nuevo: lockfile único generado (AC-22, AC-39) |
| `matriz-trader.code-workspace:1` | Nuevo: multi-root con formateadores (AC-2) |
| `.vscode/extensions.json:1` | Nuevo: recomienda Biome, Ruff y Python (AC-2) |
| `CLAUDE.md:1` | Nuevo: estructura y comandos del monorepo (AC-3) |
| `README.md:1` | Nuevo: prerrequisitos, setup, dev, compose, tests (AC-42) |
| `docker-compose.yml:1` | Nuevo: `postgres`, `backend`, `worker`, `frontend` (AC-29–AC-33, AC-43) |
| `scripts/check.sh:1` | Nuevo: gate de calidad de todos los proyectos (AC-41) |
| `scripts/check-versions.sh:1` | Nuevo: compara `.python-version`/`.nvmrc` con los `FROM` de los Dockerfiles (AC-40) |
| `model/pyproject.toml:1` | Nuevo: `matriz-model` (SQLAlchemy 2, psycopg 3, pydantic-settings, alembic) |
| `model/CLAUDE.md:1` | Nuevo (AC-3) |
| `model/src/model/__init__.py:1` | Nuevo: API pública `Base`, `create_engine_from_url`, `get_engine`, `get_sessionmaker` (AC-19) |
| `model/src/model/base.py:1` | Nuevo: `Base(DeclarativeBase)` con naming convention (AC-19, AC-20) |
| `model/src/model/db.py:1` | Nuevo: factory de engine y sesión (AC-19, AC-21) |
| `model/src/model/config.py:1` | Nuevo: `root_env_file()`, `DatabaseSettings`, `missing_env_vars()` (AC-26) |
| `model/alembic.ini:1` | Nuevo: config de Alembic (ejecución manual) |
| `model/migrations/env.py:1` | Nuevo: `target_metadata = Base.metadata`, URL desde `DATABASE_URL` |
| `model/migrations/script.py.mako:1` | Nuevo: plantilla de Alembic |
| `model/migrations/versions/0001_initial.py:1` | Nuevo: migración inicial vacía |
| `model/tests/test_base.py:1` | Nuevo: unit tests sin BD (AC-20, AC-34, AC-36) |
| `backend/pyproject.toml:1` | Nuevo: `matriz-backend` (fastapi, uvicorn, matriz-model) |
| `backend/CLAUDE.md:1` | Nuevo (AC-3) |
| `backend/Dockerfile:1` | Nuevo: imagen `python:3.13-slim` + uv (AC-30, AC-40) |
| `backend/src/backend/__init__.py:1` | Nuevo |
| `backend/src/backend/settings.py:1` | Nuevo: `BackendSettings`, `load_settings()` (AC-13, AC-46) |
| `backend/src/backend/main.py:1` | Nuevo: `create_app()` + `app` (AC-12, AC-13) |
| `backend/src/backend/health.py:1` | Nuevo: router `GET /health` (AC-10, AC-11) |
| `backend/src/backend/export_openapi.py:1` | Nuevo: escribe `frontend/openapi.json` (AC-6) |
| `backend/tests/test_health.py:1` | Nuevo (AC-10, AC-11, AC-34, AC-36) |
| `backend/tests/test_settings.py:1` | Nuevo (AC-46) |
| `backend/tests/test_openapi_snapshot.py:1` | Nuevo: falla si `frontend/openapi.json` está desactualizado (AC-6) |
| `worker/pyproject.toml:1` | Nuevo: `matriz-worker` con `matriz-client` como fuente URL (AC-16) |
| `worker/CLAUDE.md:1` | Nuevo (AC-3) |
| `worker/Dockerfile:1` | Nuevo (AC-30, AC-40) |
| `worker/src/worker/__init__.py:1` | Nuevo |
| `worker/src/worker/__main__.py:1` | Nuevo: entrypoint `python -m worker` (AC-14, AC-15) |
| `worker/src/worker/settings.py:1` | Nuevo: `WorkerSettings` con prefijo `MATRIZ_` (AC-17, AC-18) |
| `worker/src/worker/matriz_gateway.py:1` | Nuevo: adaptador tipado sobre `matriz-client` (AC-17) |
| `worker/src/worker/runner.py:1` | Nuevo: loop async con señales (AC-14, AC-15) |
| `worker/tests/test_runner.py:1` | Nuevo (AC-14, AC-15, AC-17, AC-34, AC-36) |
| `worker/tests/test_settings.py:1` | Nuevo (AC-18) |
| `stubs/matriz_client/__init__.pyi:1` | Nuevo, **solo si** el wheel no trae `py.typed` (AC-24) |
| `e2e/pyproject.toml:1` | Nuevo: `matriz-e2e` (pytest, pytest-playwright) |
| `e2e/CLAUDE.md:1` | Nuevo |
| `e2e/tests/conftest.py:1` | Nuevo: `base_url` desde `E2E_BASE_URL` (AC-38) |
| `e2e/tests/test_health_page.py:1` | Nuevo (AC-37) |
| `frontend/package.json:1` | Nuevo: dependencias y scripts (AC-4, AC-5, AC-9, AC-35) |
| `frontend/package-lock.json:1` | Nuevo: lockfile npm (AC-39) |
| `frontend/CLAUDE.md:1` | Nuevo (AC-3) |
| `frontend/index.html:1` | Nuevo |
| `frontend/vite.config.ts:1` | Nuevo: `envDir: '..'`, puerto dev y config de Vitest (AC-26, AC-28, AC-35) |
| `frontend/tsconfig.json:1` | Nuevo: referencias a `tsconfig.app.json` y `tsconfig.node.json` |
| `frontend/tsconfig.app.json:1` | Nuevo: `strict: true` |
| `frontend/tsconfig.node.json:1` | Nuevo |
| `frontend/biome.json:1` | Nuevo: formato + lint general; ignora el código generado (AC-9) |
| `frontend/eslint.config.js:1` | Nuevo: flat config, solo `react-hooks` + `react-refresh` (AC-4, AC-9) |
| `frontend/orval.config.ts:1` | Nuevo (AC-6) |
| `frontend/openapi.json:1` | Nuevo: esquema exportado y versionado (AC-5, AC-6) |
| `frontend/nginx.conf:1` | Nuevo: SPA, `/healthz` y proxy `/api/` (AC-31, AC-43) |
| `frontend/Dockerfile:1` | Nuevo: build con `node:24-alpine` y runtime nginx (AC-30, AC-40) |
| `frontend/src/main.tsx:1` | Nuevo: `QueryClientProvider` + `ConfigProvider` + `RouterProvider` |
| `frontend/src/router.tsx:1` | Nuevo: `createBrowserRouter` con `/` (AC-7) |
| `frontend/src/queryClient.ts:1` | Nuevo: retry/timeout (AC-8) |
| `frontend/src/api/http.ts:1` | Nuevo: mutator `customFetch` + `ApiError` (AC-8) |
| `frontend/src/pages/HealthPage.tsx:1` | Nuevo (AC-7, AC-8, AC-45) |
| `frontend/src/pages/HealthPage.test.tsx:1` | Nuevo (AC-35) |
| `frontend/src/test/setup.ts:1` | Nuevo: jest-dom + polyfill de `matchMedia` |
| `frontend/src/vite-env.d.ts:1` | Nuevo: tipa `VITE_API_BASE_URL` |

## Root & tooling changes

Workspace `uv` en la raíz. El proyecto raíz depende de todos los miembros, así que un `uv sync` sin flags instala todo, incluido `matriz-client` (AC-16, AC-22):

```toml
# pyproject.toml
[project]
name = "matriz-trader"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = ["matriz-model", "matriz-backend", "matriz-worker", "matriz-e2e"]

[dependency-groups]
dev = ["ruff", "pyright", "pytest", "pytest-asyncio"]

[tool.uv]
package = false

[tool.uv.workspace]
members = ["model", "backend", "worker", "e2e"]

[tool.uv.sources]
matriz-model = { workspace = true }
matriz-backend = { workspace = true }
matriz-worker = { workspace = true }
matriz-e2e = { workspace = true }

[tool.ruff]
target-version = "py313"
line-length = 100
extend-exclude = ["frontend"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "SIM", "RUF", "ASYNC", "PT"]

[tool.pyright]
include = ["model", "backend", "worker", "e2e"]
exclude = ["**/.venv", "**/__pycache__"]
typeCheckingMode = "strict"
pythonVersion = "3.13"
venvPath = "."
venv = ".venv"
stubPath = "stubs"
```

Cada miembro usa layout `src/` con hatchling, un nombre de distribución `matriz-*` y un paquete importable corto (`import model`, `import backend`, `import worker`):

```toml
# model/pyproject.toml (backend/worker/e2e siguen el mismo patrón)
[project]
name = "matriz-model"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = ["sqlalchemy>=2.0", "psycopg[binary]>=3.2", "pydantic-settings>=2.4", "alembic>=1.13"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/model"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--import-mode=importlib"
```

```toml
# worker/pyproject.toml (fragmento) — AC-16
[project]
name = "matriz-worker"
dependencies = ["matriz-model", "matriz-client==0.3.0", "pydantic-settings>=2.4"]

[tool.uv.sources]
matriz-model = { workspace = true }
matriz-client = { url = "https://github.com/gravity-quant/market-libs/releases/download/matriz-client-v0.3.0/matriz_client-0.3.0-py3-none-any.whl" }
```

`.env.example` (AC-25, AC-44). Los nombres `MATRIZ_*` se ajustan a lo que encuentre T4:

```dotenv
# --- PostgreSQL (docker compose + dev) ---
POSTGRES_USER=matriz
POSTGRES_PASSWORD=changeme
POSTGRES_DB=matriz_trader
POSTGRES_PORT=5432
# URL usada por backend/worker/alembic en modo dev (en compose se sobreescribe con host "postgres")
DATABASE_URL=postgresql+psycopg://matriz:changeme@localhost:5432/matriz_trader

# --- Backend ---
BACKEND_PORT=8000
# Orígenes CORS separados por coma (servidor dev del frontend)
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO

# --- Frontend ---
FRONTEND_DEV_PORT=5173
# URL base de la API en dev; el build de producción usa /api (nginx)
VITE_API_BASE_URL=http://localhost:8000
# Puerto publicado por nginx en docker compose
FRONTEND_PORT=8080

# --- Worker / matriz-client ---
MATRIZ_BASE_URL=https://sandbox.example.invalid
MATRIZ_USERNAME=changeme
MATRIZ_PASSWORD=changeme
# Opcional, solo si matriz-client lo requiere
MATRIZ_ACCOUNT=
WORKER_HEARTBEAT_SECONDS=30

# --- Tests de integración ---
E2E_BASE_URL=http://localhost:8080
```

VS Code (AC-2):

```jsonc
// matriz-trader.code-workspace
{
  "folders": [
    { "name": "root", "path": "." },
    { "name": "frontend", "path": "frontend" },
    { "name": "backend", "path": "backend" },
    { "name": "worker", "path": "worker" },
    { "name": "model", "path": "model" },
    { "name": "e2e", "path": "e2e" }
  ],
  "settings": {
    "editor.formatOnSave": true,
    "[typescript]": { "editor.defaultFormatter": "biomejs.biome" },
    "[typescriptreact]": { "editor.defaultFormatter": "biomejs.biome" },
    "[json]": { "editor.defaultFormatter": "biomejs.biome" },
    "[python]": { "editor.defaultFormatter": "charliermarsh.ruff" },
    "python.defaultInterpreterPath": "${workspaceFolder:root}/.venv/bin/python",
    "python.analysis.typeCheckingMode": "strict"
  },
  "extensions": { "recommendations": ["biomejs.biome", "charliermarsh.ruff", "ms-python.python"] }
}
```

## Model changes

```python
# model/src/model/config.py
def root_env_file() -> Path | None:
    """Primer `.env` encontrado subiendo desde este archivo; None dentro de Docker."""

class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")
    database_url: str  # DATABASE_URL, obligatoria

def missing_env_vars(exc: ValidationError) -> list[str]:
    """Nombres de env en MAYÚSCULAS de los errores `type == "missing"`, ordenados."""
```

```python
# model/src/model/base.py — AC-19, AC-20
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
```

```python
# model/src/model/db.py — AC-19, AC-11, AC-21
def create_engine_from_url(url: str) -> Engine:
    # pool_pre_ping=True, pool_timeout=2, connect_args={"connect_timeout": 3}
def get_engine() -> Engine:                     # singleton lazy, usa DatabaseSettings().database_url
def get_sessionmaker(engine: Engine) -> sessionmaker[Session]:  # expire_on_commit=False
```

Alembic (Resolved Decision: configurado, ejecución manual, sin hook en Compose): `model/alembic.ini` con `script_location = %(here)s/migrations`; `env.py` toma `DatabaseSettings().database_url` y usa `target_metadata = Base.metadata`; la revisión `0001_initial` tiene `upgrade()` y `downgrade()` vacíos. Se ejecuta con `uv run alembic -c model/alembic.ini upgrade head`.

## Backend changes

```python
# backend/src/backend/settings.py — AC-13, AC-46
class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")
    database_url: str            # DATABASE_URL (obligatoria)
    cors_origins: str = ""       # CORS_ORIGINS, separados por coma
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]: ...   # split(","), strip, sin vacíos

def load_settings() -> BackendSettings:
    # ValidationError → log ERROR "Missing required environment variables: DATABASE_URL" → raise SystemExit(2)
```

```python
# backend/src/backend/health.py — AC-10, AC-11
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]

DbProbe = Callable[[], bool]

def get_db_probe(request: Request) -> DbProbe: ...   # ping SELECT 1 sobre request.app.state.engine; SQLAlchemyError → False

@router.get(
    "/health",
    operation_id="getHealth",
    tags=["health"],
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
)
def get_health(response: Response, probe: Annotated[DbProbe, Depends(get_db_probe)]) -> HealthResponse:
    # ok → 200 {"status": "ok", "database": "ok"}
    # fail → 503 {"status": "degraded", "database": "unavailable"}
```

```python
# backend/src/backend/main.py — AC-12, AC-13
def create_app(settings: BackendSettings) -> FastAPI:
    # title="Matriz Trader API", version="0.1.0"; app.state.engine = create_engine_from_url(settings.database_url)
    # CORSMiddleware(allow_origins=settings.cors_origin_list, allow_methods=["GET"], allow_headers=["*"]) solo si la lista no está vacía
    # include_router(health.router); /openapi.json queda en la ruta por defecto de FastAPI

app = create_app(load_settings())
```

```python
# backend/src/backend/export_openapi.py — AC-6
# uv run python -m backend.export_openapi [ruta]   (default: <repo>/frontend/openapi.json)
# create_app(BackendSettings(database_url="postgresql+psycopg://export@localhost/export")) — no conecta
# json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
```

Respuesta de `GET /health`:

```json
{ "status": "ok", "database": "ok" }
```

## Worker changes

```python
# worker/src/worker/settings.py — AC-17, AC-18
class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")
    matriz_base_url: str
    matriz_username: str
    matriz_password: SecretStr
    matriz_account: str | None = None
    worker_heartbeat_seconds: float = 30.0
    log_level: str = "INFO"
```

```python
# worker/src/worker/matriz_gateway.py — AC-17
class MatrizGateway(Protocol):
    def connect(self) -> None: ...      # lanza si la conexión o autenticación falla
    def close(self) -> None: ...

class MatrizClientGateway:              # única clase que importa matriz_client
    def __init__(self, settings: WorkerSettings) -> None: ...
```

```python
# worker/src/worker/runner.py — AC-14, AC-15
async def run(gateway: MatrizGateway, settings: WorkerSettings, stop: asyncio.Event) -> int:
    # connect() → INFO "matriz-client initialized (base_url=%s)" | ERROR "matriz-client initialization failed: %s" → return 1
    # loop: await asyncio.wait_for(stop.wait(), timeout=heartbeat) → INFO "worker heartbeat"
    # stop → gateway.close() → INFO "worker stopped" → return 0

# worker/src/worker/__main__.py
def main() -> int:
    # load settings (falta → ERROR "Missing required environment variables: MATRIZ_PASSWORD, MATRIZ_USERNAME", return 2)
    # loop.add_signal_handler(SIGINT|SIGTERM, stop.set); return asyncio.run(...)
```

## Frontend changes

Scripts de `package.json` (AC-4, AC-5, AC-9, AC-35). El cliente generado no se versiona: se regenera antes de cada comando que lo necesita.

```json
{
  "type": "module",
  "engines": { "node": ">=24 <25" },
  "scripts": {
    "generate:api": "orval --config orval.config.ts",
    "predev": "npm run generate:api",
    "dev": "vite",
    "prebuild": "npm run generate:api",
    "build": "tsc -b && vite build",
    "pretypecheck": "npm run generate:api",
    "typecheck": "tsc -b",
    "lint": "biome lint . && eslint .",
    "format": "biome format --write .",
    "format:check": "biome format .",
    "pretest": "npm run generate:api",
    "test": "vitest run"
  }
}
```

Dependencias: `react`, `react-dom`, `react-router` (v7, modo data), `@tanstack/react-query`, `antd`. Dev: `vite`, `@vitejs/plugin-react`, `typescript`, `orval`, `@biomejs/biome`, `eslint` (último major estable), `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `globals`, `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`. Las versiones exactas quedan fijadas en `package-lock.json`.

```ts
// frontend/orval.config.ts — AC-6
export default defineConfig({
  matriz: {
    input: { target: './openapi.json' },
    output: {
      target: 'src/api/generated/matriz.ts',
      schemas: 'src/api/generated/model',
      client: 'react-query',
      httpClient: 'fetch',
      clean: true,
      override: { mutator: { path: './src/api/http.ts', name: 'customFetch' } },
    },
  },
});
```

```ts
// frontend/src/api/http.ts — AC-8
export class ApiError extends Error {
  constructor(public readonly status: number, public readonly body: unknown) { super(`HTTP ${status}`); }
}
export const REQUEST_TIMEOUT_MS = 5000;
export async function customFetch<T>(url: string, options: RequestInit): Promise<T>;
// URL = import.meta.env.VITE_API_BASE_URL + url
// signal = AbortSignal.any([options.signal, AbortSignal.timeout(REQUEST_TIMEOUT_MS)].filter(Boolean))
// !res.ok → throw new ApiError(res.status, body JSON o null)
// ok → devuelve la forma que espera el código generado por Orval ({ data, status, headers }), verificada contra la versión instalada
```

```ts
// frontend/src/queryClient.ts — AC-8 (peor caso 5 s + 1 s + 5 s = 11 s < 15 s)
new QueryClient({ defaultOptions: { queries: { retry: 1, retryDelay: 1000, refetchOnWindowFocus: false } } });
```

`HealthPage` (ruta `/`, AC-7, AC-8, AC-45). Los `data-testid` son contrato de los tests:

| Estado | Componente antd | `data-testid` | Copy |
|--------|-----------------|---------------|------|
| Cargando | `<Spin size="large" />` + `Typography.Text` | `health-loading` | "Consultando estado del backend…" |
| OK | `<Descriptions title="Estado del sistema" bordered column={1}>` con `Tag` por fila | `health-status`, `health-database` | Etiquetas `status` y `database`; valor literal del JSON |
| Error | `<Alert type="error" showIcon>` | `health-error` | message: "No se pudo obtener el estado del backend"; description: `ApiError` 503 → "HTTP 503 — database: unavailable"; otro `ApiError` → "HTTP {status}"; red o timeout → "El backend no responde" |

El layout es `Layout` > `Layout.Content` con padding 24 y el título `Typography.Title level={2}` "Matriz Trader".

## Docker & Compose changes

```yaml
# docker-compose.yml — AC-29..AC-33, AC-43
name: matriz-trader
services:
  postgres:
    image: postgres:17-alpine
    env_file: .env
    ports: ["${POSTGRES_PORT:-5432}:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
  backend:
    build: { context: ., dockerfile: backend/Dockerfile }
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    depends_on: { postgres: { condition: service_healthy } }
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
  worker:
    build: { context: ., dockerfile: worker/Dockerfile }
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    depends_on: { postgres: { condition: service_healthy } }
    restart: on-failure:3
    stop_grace_period: 10s
  frontend:
    build: { context: ., dockerfile: frontend/Dockerfile }
    ports: ["${FRONTEND_PORT:-8080}:80"]
    depends_on: { backend: { condition: service_healthy } }
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1/healthz"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  pgdata: {}
```

```nginx
# frontend/nginx.conf — AC-31
server {
  listen 80;
  root /usr/share/nginx/html;
  location = /healthz { access_log off; return 200 "ok"; }
  location /api/ { proxy_pass http://backend:8000/; }
  location / { try_files $uri /index.html; }
}
```

Los Dockerfiles de Python usan `FROM python:3.13-slim`, copian `uv` desde `ghcr.io/astral-sh/uv:<versión fija>`, copian `pyproject.toml`, `uv.lock` y el `pyproject.toml` de **todos** los miembros, y corren `uv sync --frozen --no-dev --package matriz-<x> --no-install-workspace`. Después copian `model/` y el código del servicio y vuelven a correr `uv sync --frozen --no-dev --package matriz-<x>`. El `CMD` va en forma exec: backend `["/app/.venv/bin/uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]`, worker `["/app/.venv/bin/python","-m","worker"]`. El frontend se construye en `node:24-alpine` (`npm ci` + `npm run build` con `ENV VITE_API_BASE_URL=/api`) y se sirve desde `nginx:1.27-alpine`.

## Key implementation details

- **Lectura del `.env` (AC-26):** pydantic-settings usa `env_file=root_env_file()`, que sube desde el archivo fuente hasta encontrar `.env`. En Docker no hay `.env` en la imagen (`.dockerignore`); las variables llegan por `env_file: .env` de Compose. Vite usa `envDir: '..'`, y `vite.config.ts` usa `loadEnv(mode, '..', '')` para `FRONTEND_DEV_PORT` con `strictPort: true`. No existen `.env` por proyecto.
- **Precedencia:** una variable de entorno real gana sobre `.env` (comportamiento por defecto de pydantic-settings). Así Compose sobreescribe `DATABASE_URL` con el host `postgres`.
- **`POSTGRES_PASSWORD` en la URL:** debe ser URL-safe; el README lo advierte.
- **Mensajes de env faltante (AC-18, AC-46):** el formato exacto es `Missing required environment variables: A, B`, con los nombres en mayúsculas y en orden alfabético. Exit code `2` en ambos servicios. El worker sale con `1` si falla la conexión a Matriz.
- **Worker (Resolved Decision: conexión real, fail-fast):** `connect()` se ejecuta antes del loop. Si falla, se loguea el error y el proceso sale con `1`. `restart: on-failure:3` acota el bucle de reinicios en Compose.
- **Señales (AC-15):** `loop.add_signal_handler` para `SIGINT` y `SIGTERM` setea un único `asyncio.Event`. `gateway.close()` corre con `asyncio.wait_for(asyncio.to_thread(...), 5)`. El exit code es `0`. El `CMD` en forma exec garantiza que PID 1 sea Python.
- **Logging Python:** `logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s", stream=sys.stdout)`. Las contraseñas son `SecretStr` y nunca se loguean.
- **Health (AC-11):** el handler es `def` sync (corre en el threadpool). `connect_timeout=3` + `pool_timeout=2` mantiene la respuesta por debajo de 5 s. El engine se crea en `create_app` sin conectar, así el backend arranca aunque Postgres esté caído.
- **`status` en 503:** se usa `"degraded"`, porque AC-11 no fija el valor (ver Open Questions).
- **CORS (AC-13):** se configura solo si `CORS_ORIGINS` no está vacío. En Compose no hace falta (mismo origen vía nginx).
- **Contrato OpenAPI (AC-6, AC-12):** `operation_id="getHealth"` → hook `useGetHealth`. `frontend/openapi.json` se regenera con `uv run python -m backend.export_openapi` y se commitea. `backend/tests/test_openapi_snapshot.py` compara byte a byte y falla si el archivo quedó desactualizado.
- **Lint TS (AC-9):** Biome 2 hace formato y lint general (`recommended`). ESLint (flat config) solo carga el parser de `typescript-eslint` y las reglas `react-hooks/*` y `react-refresh/only-export-components`, sin `js.configs.recommended`, para no solapar con Biome. Ambos ignoran `dist/` y `src/api/generated/`.
- **Tests de frontend (AC-35, AC-36):** Vitest con `environment: 'jsdom'`. `src/test/setup.ts` importa `@testing-library/jest-dom/vitest` y define `window.matchMedia`, que antd necesita. `fetch` se mockea con `vi.stubGlobal`, y cada test usa un `QueryClient` con `retry: false`.
- **Tests de Python sin infraestructura (AC-36):** backend usa `app.dependency_overrides[get_db_probe]` y settings construidas a mano; worker usa un `FakeGateway`; model solo inspecciona `Base.metadata` y `engine.dialect.name == "postgresql"` sin conectar. Los tests de settings pasan `_env_file=None` y limpian el entorno con `monkeypatch.delenv`.
- **Pyright strict + `matriz-client` (AC-24):** si el wheel no trae `py.typed`, se agrega `stubs/matriz_client/__init__.pyi` con solo los símbolos que usa `MatrizClientGateway`. No se usan `# type: ignore` globales.
- **e2e (AC-37, AC-38):** `conftest.py` define el fixture `base_url` con `os.environ.get("E2E_BASE_URL", "http://localhost:8080")`. El test hace `page.goto(base_url + "/")` y luego `expect(page.get_by_test_id("health-status")).to_have_text("ok", timeout=30_000)`, y lo mismo para `health-database`. Antes de la primera ejecución se corre `uv run playwright install chromium`.
- **Versiones (AC-40):** `.python-version` = `3.13` y `.nvmrc` = `24`. `scripts/check-versions.sh` sale con código distinto de 0 si algún `FROM python:`/`FROM node:` o `engines.node` no coincide.
- **Git:** el directorio aún no es repositorio. T1 ejecuta `git init` para que `.gitignore` y los lockfiles tengan efecto (AC-27, AC-39).

## Risks & rollback

| Risk | Mitigation | How to revert |
|------|------------|---------------|
| `gravity-quant/market-libs` es privado y `uv sync`/`docker build` fallan con 404 | T4 lo verifica primero. Si es privado: token en `~/.netrc` en local y `RUN --mount=type=secret,id=github_token` + `secrets:` en Compose, nunca `ARG`/`ENV` (AC-44) | Quitar la fuente URL de `worker/pyproject.toml` y `uv lock` |
| La API real de `matriz-client` no coincide con el adaptador | Todo el acoplamiento vive en `MatrizClientGateway`; T4 documenta la firma antes de T8 | Revertir solo `matriz_gateway.py` |
| `matriz-client` sin tipos rompe Pyright strict | Stub local `.pyi` mínimo en `stubs/` | Borrar `stubs/` |
| Worker fail-fast + Matriz inaccesible → reinicios que violan AC-43 | `restart: on-failure:3` acota el bucle y queda registrado en Open Questions | Cambiar `restart` o pasar a reintento con backoff en `runner.py` |
| `openapi.json` desactualizado respecto del backend | Snapshot test en backend que falla en CI/local | Correr `export_openapi` y commitear |
| La forma de respuesta del mutator de Orval cambia entre versiones | Versión fijada en `package-lock.json`; los tests de `HealthPage` cubren el contrato | Ajustar `http.ts` |
| antd en jsdom falla por `matchMedia` | Polyfill en `src/test/setup.ts` | — |
| Contraseña con caracteres especiales rompe `DATABASE_URL` en Compose | Documentar que sea URL-safe; el ejemplo usa `changeme` | — |

Rollback general: el ticket es greenfield, así que revertir es eliminar los archivos nuevos (o el commit inicial). No hay datos ni migraciones aplicadas que deshacer.

## Verification

| AC | Cómo se prueba |
|----|----------------|
| AC-1 | `ls -d frontend backend worker model` en un clon limpio |
| AC-2 | Abrir `matriz-trader.code-workspace`: aparecen las carpetas y `[typescript]`/`[python]` tienen formateador Biome/Ruff |
| AC-3 | Existen `CLAUDE.md` en la raíz y en los 4 proyectos, con secciones de dev/lint/test |
| AC-4 | `cd frontend && npm ci` exit 0; `package.json` lista las dependencias; existe `eslint.config.js` |
| AC-5 | Con el backend apagado: `cd frontend && npm run build` exit 0 |
| AC-6 | `npm run generate:api` crea `src/api/generated/matriz.ts` con `useGetHealth`; `test_openapi_snapshot.py` pasa |
| AC-7 | Test Vitest "muestra status y database ok" + e2e `test_health_page.py` |
| AC-8 | Test Vitest con fetch → 503 renderiza `health-error`; manual: backend apagado → Alert en < 15 s |
| AC-9 | `npm run lint && npm run format:check` exit 0 |
| AC-10 | `backend/tests/test_health.py::test_health_ok` (200 + body) y esquema `HealthResponse` en `/openapi.json` |
| AC-11 | `test_health_db_unavailable` (503 + `database: "unavailable"`); manual: `docker compose stop postgres` y `time curl` < 5 s |
| AC-12 | `test_openapi_served` (`GET /openapi.json` 200) y Orval lo consume |
| AC-13 | `test_cors_preflight` con `CORS_ORIGINS=http://localhost:5173` devuelve `access-control-allow-origin` |
| AC-14 | `worker/tests/test_runner.py::test_runs_until_stop`: sigue corriendo tras N heartbeats hasta que se setea `stop` |
| AC-15 | `test_stop_returns_zero` (< 10 s); manual: `docker compose stop worker` → exit 0 |
| AC-16 | `uv sync && uv run python -c "import matriz_client"`; `uv.lock` contiene la URL del wheel |
| AC-17 | `test_logs_initialization_result` (caplog con "matriz-client initialized") |
| AC-18 | `worker/tests/test_settings.py`: env vacío → exit 2 y log con los nombres faltantes |
| AC-19 | `model/tests/test_base.py`: `issubclass(Base, DeclarativeBase)` y `create_engine_from_url` → dialecto postgresql |
| AC-20 | Test con un modelo de ejemplo `Mapped[]`/`mapped_column()`; sin plugins en `pyproject.toml` |
| AC-21 | Solo existe el driver `psycopg` / dialecto postgresql; compose y e2e usan `postgres` |
| AC-22 | `uv sync` en la raíz → un único `uv.lock` con los 4 miembros |
| AC-23 | `uv run ruff check . && uv run ruff format --check .` exit 0 |
| AC-24 | `uv run pyright` → `0 errors` con `typeCheckingMode = "strict"` |
| AC-25 | Revisión de `.env.example` contra las variables que leen los settings, Vite y Compose |
| AC-26 | No existen `*/.env`; los settings usan `root_env_file()` y Vite usa `envDir: '..'` |
| AC-27 | `git check-ignore .env` → match; `git ls-files .env.example` → listado |
| AC-28 | `npm run dev` (HMR), `uv run uvicorn backend.main:app --reload`, `uv run python -m worker` arrancan aislados |
| AC-29 | `docker compose up postgres` levanta solo postgres en `${POSTGRES_PORT}` |
| AC-30 | `docker compose up --build` → 4 servicios creados |
| AC-31 | Tras `docker compose up`, `pytest e2e` pasa en < 120 s |
| AC-32 | `docker compose config` muestra `depends_on.postgres.condition: service_healthy` en backend y worker |
| AC-33 | Crear una tabla manualmente, `docker compose down` + `up`: la tabla persiste en el volumen `pgdata` |
| AC-34 | `uv run pytest` en `backend/`, `worker/`, `model/` exit 0 |
| AC-35 | `cd frontend && npm test` exit 0 (3 tests de `HealthPage`) |
| AC-36 | Unit tests ejecutados con Docker detenido y sin red: pasan |
| AC-37 | `uv run pytest e2e` con el stack levantado: pasa en Chromium headless |
| AC-38 | `E2E_BASE_URL=http://localhost:9999 uv run pytest e2e` → exit ≠ 0 |
| AC-39 | `uv.lock` y `frontend/package-lock.json` versionados |
| AC-40 | `scripts/check-versions.sh` exit 0 |
| AC-41 | `scripts/check.sh` (ruff, ruff format, pyright, pytest ×3, npm lint/format:check/typecheck/test) exit 0 |
| AC-42 | El README contiene las secciones Prerrequisitos, Setup, Dev, Docker Compose y Tests |
| AC-43 | `docker compose ps` en < 120 s: postgres/backend/frontend `healthy` y worker `running` con `RestartCount=0` (requiere Matriz accesible) |
| AC-44 | `.env.example` solo tiene `changeme`/URLs de ejemplo; `git ls-files` no incluye `.env` |
| AC-45 | Test Vitest con fetch pendiente renderiza `health-loading` |
| AC-46 | `backend/tests/test_settings.py`: sin `DATABASE_URL` → `SystemExit(2)` y log "Missing required environment variables: DATABASE_URL" |

## Tasks

### Wave 1

- [ ] T1: Crear la configuración raíz (`git init`, `.gitignore`, `.env.example`, `.python-version`, `.nvmrc`, `.dockerignore`) — _outcome: `git check-ignore .env` coincide y `.env.example` contiene todas las variables del plan solo con valores de ejemplo (AC-25, AC-27, AC-44)_
- [ ] T2: Scaffold de `frontend/` con Vite + React + TS strict, antd, react-router, react-query, Biome, ESLint flat config y Vitest, con una página placeholder — _outcome: `npm ci && npm run lint && npm run format:check` termina con exit 0 y genera `package-lock.json` (AC-4, AC-9, AC-39)_
- [ ] T3: Crear `matriz-trader.code-workspace` y `.vscode/extensions.json` — _outcome: al abrir el workspace aparecen frontend/backend/worker/model y Biome/Ruff quedan como formateadores por defecto (AC-1, AC-2)_
- [ ] T4: Descargar el wheel de `matriz-client` 0.3.0 a un directorio temporal aislado, verificar si la URL responde sin credenciales e inspeccionar el constructor, los métodos de conexión y cierre, los parámetros requeridos y `py.typed` — _outcome: `.octo/specs/initial-setup/matriz-client-notes.md` documenta público/privado, la firma real y los nombres finales de las variables `MATRIZ_*` (AC-16, AC-17)_

### Wave 2 (depends on T1, T4)

- [ ] T5: Crear el `pyproject.toml` raíz (workspace, Ruff, Pyright strict), los `pyproject.toml` de `model`, `backend`, `worker` y `e2e` con paquetes vacíos, y la fuente URL de `matriz-client` — _outcome: `uv sync` genera un único `uv.lock` y `uv run python -c "import matriz_client"` funciona (AC-16, AC-22, AC-39)_

### Wave 3 (depends on T5)

- [ ] T6: Implementar `model` (`config.py`, `base.py`, `db.py`, Alembic con `0001_initial` vacía) y sus unit tests — _outcome: `cd model && uv run pytest` pasa sin Postgres y `import model` expone `Base` y los factories (AC-19, AC-20, AC-21, AC-34, AC-36)_

### Wave 4 (depends on T6)

- [ ] T7: Implementar el backend (`settings.py`, `health.py`, `main.py`, `export_openapi.py`) con tests de health, CORS, OpenAPI y env faltante — _outcome: `cd backend && uv run pytest` pasa cubriendo 200/503, CORS y `SystemExit(2)` (AC-10, AC-11, AC-12, AC-13, AC-34, AC-46)_
- [ ] T8: Implementar el worker (`settings.py`, `matriz_gateway.py` según T4, `runner.py`, `__main__.py`, stub `.pyi` si hace falta) con tests de loop, señales y env faltante — _outcome: `cd worker && uv run pytest` pasa con `FakeGateway`, y `uv run pyright worker` reporta 0 errores (AC-14, AC-15, AC-17, AC-18, AC-24, AC-34, AC-36)_

### Wave 5 (depends on T2, T7, T8)

- [ ] T9: Exportar `frontend/openapi.json`, configurar Orval + `http.ts` + `queryClient.ts` + router, implementar `HealthPage` con sus 3 tests y agregar `backend/tests/test_openapi_snapshot.py` — _outcome: con el backend apagado, `npm run build` y `npm test` terminan con exit 0, y la página muestra `health-loading`/`health-status`/`health-error` según el estado (AC-5, AC-6, AC-7, AC-8, AC-35, AC-45)_
- [ ] T10: Crear `backend/Dockerfile`, `worker/Dockerfile` y `docker-compose.yml` con `postgres`, `backend` y `worker` (healthchecks, `depends_on`, volumen `pgdata`) — _outcome: `docker compose up --build postgres backend worker` deja backend `healthy` y `curl` dentro de la red devuelve `{"status":"ok","database":"ok"}` (AC-29, AC-32, AC-33, AC-40)_

### Wave 6 (depends on T9, T10)

- [ ] T11: Crear `frontend/Dockerfile` y `frontend/nginx.conf`, y agregar el servicio `frontend` a `docker-compose.yml` — _outcome: `docker compose up --build` levanta los 4 servicios y `http://localhost:8080/` muestra `status: ok` y `database: ok` en menos de 120 s (AC-30, AC-31, AC-43)_

### Wave 7 (depends on T11)

- [ ] T12: Implementar `e2e/tests/conftest.py` y `test_health_page.py` con Playwright — _outcome: con el stack levantado, `uv run pytest e2e` pasa, y con `E2E_BASE_URL` inválida termina con exit ≠ 0 (AC-37, AC-38)_
- [ ] T13: Crear `scripts/check.sh` (todos los gates) y `scripts/check-versions.sh` — _outcome: ambos scripts terminan con exit 0 sobre el repo (AC-23, AC-24, AC-40, AC-41)_
- [ ] T14: Escribir `README.md` y los `CLAUDE.md` de la raíz, `frontend`, `backend`, `worker`, `model` y `e2e` con los comandos verificados — _outcome: cada comando documentado se ejecuta tal cual sobre un clon limpio (AC-3, AC-28, AC-42)_

## Open Questions

- **Orval — decisiones resueltas contradictorias:** una dice "versionar el código generado" y la posterior "versionar `openapi.json` y generar en el build". El plan sigue la **posterior**: el código generado queda en `.gitignore`. Confirmar.
- **Worker fail-fast vs AC-43:** la decisión resuelta (conectarse y salir ≠ 0 si falla) hace que AC-43 ("running sin reinicios") dependa de que Matriz esté accesible. El plan acota los reinicios con `restart: on-failure:3`. Revisar si conviene reintento con backoff.
- **Acceso al wheel:** no se verificó si `gravity-quant/market-libs` es público; lo resuelve T4. Si es privado se aplica el esquema netrc + Docker build secret descrito en Risks.
- **Variables de `matriz-client`:** `MATRIZ_BASE_URL/USERNAME/PASSWORD/ACCOUNT` son provisionales hasta T4.
- **`status` en la respuesta 503:** AC-11 no lo fija; el plan usa `"degraded"`.
- **Producción del frontend:** se eligió nginx con proxy `/api/` (pregunta abierta en requirements).
- **ESLint + Biome:** Biome para formato y lint general; ESLint solo para `react-hooks` y `react-refresh`.
- **Runner de frontend:** Vitest + Testing Library + jsdom.
- **Versiones:** Python 3.13 y Node 24 LTS por defecto.
- **"vsclaude":** se interpretó como VS Code + Claude Code (AC-2, AC-3).
- **Copy de la UI en español:** se asumió español para los textos de `HealthPage`.

## Critical Decisions

### Critical Decision — T1: ignorar también `.env.*`
**What:** `.gitignore` y `.dockerignore` excluyen `.env` y `.env.*`, con la excepción `!.env.example`; `.dockerignore` además excluye `.claude`, `.vscode` y los caches de Ruff/pytest/Playwright.
**Why:** evita versionar o meter en la imagen variantes locales como `.env.local` con secretos reales (AC-44), sin dejar de versionar `.env.example` (AC-27).
**Affects:** `.gitignore`, `.dockerignore`; los Dockerfiles de T10/T11 no pueden depender de esas rutas.

### Critical Decision — T2: scripts sin pre-hooks de Orval y página placeholder `HomePage`
**What:** `package.json` aún no tiene `generate:api` ni los `pre*` de Orval (Orval queda instalado, pero sin `orval.config.ts`). La ruta `/` renderiza un `src/pages/HomePage.tsx` placeholder con un test de Vitest, y `src/test/setup.ts` (jest-dom + `matchMedia`) se crea ya en T2.
**Why:** `frontend/openapi.json` recién existe en T9; si los pre-hooks estuvieran ahora, `build`/`test` fallarían. Además, `vitest run` sin tests termina con exit ≠ 0.
**Affects:** T9 agrega `generate:api` + `predev`/`prebuild`/`pretypecheck`/`pretest`, reemplaza `HomePage` por `HealthPage` en `src/router.tsx` y crea `queryClient.ts` (hoy `main.tsx` usa un `new QueryClient()` por defecto).

### Critical Decision — T2: últimos majors del registry, con TypeScript fijado en 6.0
**What:** todas las dependencias se instalaron con `@latest` (2026-10-30): ESLint 10, Biome 2.6 (config migrada con `biome migrate`: `rules.preset`), Vite 8, `@vitejs/plugin-react` 6, Vitest 5, React 19.3, antd 6, react-router 8, Orval 8, jsdom 30. Hay dos excepciones: `typescript` va en `~6.0.3` en vez de 7.x y `@types/node` en `^24`. `eslint.config.js` declara las reglas `react-hooks/*` a mano, sin preset.
**Why:** `typescript-eslint` 8.72 exige `typescript >=4.8.4 <6.1.0`, y `@types/node` tiene que coincidir con Node 24 (`.nvmrc`, AC-40). Las reglas manuales evitan depender del nombre del preset en cada versión del plugin.
**Affects:** `frontend/package.json`, `frontend/package-lock.json`, `frontend/biome.json`. T9 tiene que usar las APIs de react-router 8, antd 6 y Orval 8, y verificar contra Orval 8 la forma de respuesta del mutator. Pasar a TS 7 queda bloqueado hasta que `typescript-eslint` lo soporte. Si `NODE_ENV=production` está en el entorno, `npm ci` omite las devDependencies: correrlo sin esa variable o con `--include=dev` (documentarlo en T14).

### Critical Decision — T3: Biome también para `[javascript]` y `[jsonc]`
**What:** además de `[typescript]`, `[typescriptreact]` y `[json]`, `matriz-trader.code-workspace` asigna Biome como formateador de `[javascript]` y `[jsonc]`.
**Why:** `biome format .` (AC-9) también cubre `eslint.config.js` y los `tsconfig*.json`, que VS Code abre como `jsonc`. Sin esto, format-on-save usaría otro formateador y `format:check` fallaría.
**Affects:** `matriz-trader.code-workspace`.

### Critical Decision — T4: variables `MATRIZ_*` finales, sin `MATRIZ_ACCOUNT` y sin stub
**What:** el wheel es público (HTTP 200 sin credenciales) y trae `py.typed`, con 0 errores en Pyright strict. Las variables finales son `MATRIZ_BASE_URL` (ejemplo `https://api.remarkets.primary.com.ar`), `MATRIZ_USERNAME` y `MATRIZ_PASSWORD`, y se elimina `MATRIZ_ACCOUNT`. `connect()` del gateway llama a `Client.login()`, porque la librería no tiene `connect()`, y `close()` llama a `Client.close()`. Los fallos de red llegan como `httpx.HTTPError`, que no es `MatrizClientError`.
**Why:** `Client(*, base_url, username, password, ...)` no recibe cuenta (es un argumento por llamada) y, si un argumento es `None`, cae a `PRIMARY_*` del entorno. Además la librería ejecuta `load_dotenv()` al importarse. Detalle en `matriz-client-notes.md`.
**Affects:** T5 (sin token ni secret de Docker; no hace falta `stubs/`), T8 (`settings.py` sin `matriz_account`, `matriz_gateway.py` captura `MatrizClientError | httpx.HTTPError`, el import de `matriz_client` queda aislado en el gateway), `.env.example` (quitar `MATRIZ_ACCOUNT` y usar la URL de reMarkets) y T10 (los Dockerfiles no necesitan `secrets:`).

### Critical Decision — T5: Ruff excluye `.octo`, `e2e` es paquete y `httpx` es dependencia directa del worker
**What:** `[tool.ruff] extend-exclude = ["frontend", ".octo"]`. `e2e` tiene un paquete vacío `src/e2e/__init__.py` (hatchling) igual que los demás miembros. `worker/pyproject.toml` declara `httpx>=0.27`. Las herramientas de dev (`ruff`, `pyright`, `pytest`, `pytest-asyncio`) llevan cotas mínimas en el grupo `dev` de la raíz, y las versiones exactas quedan en `uv.lock`.
**Why:** Ruff 0.17 formatea los bloques de Python dentro de Markdown, y `ruff format --check .` fallaba sobre `plan.md` y `matriz-client-notes.md` (AC-23). La raíz depende de `matriz-e2e`, así que `e2e` tiene que ser un paquete instalable. El gateway de T8 captura `httpx.HTTPError`, y con Pyright strict ese import tiene que ser una dependencia declarada, no transitiva.
**Affects:** `pyproject.toml`, `e2e/pyproject.toml`, `worker/pyproject.toml`. Los Dockerfiles de T10 copian el `pyproject.toml` de los 4 miembros. Las dependencias de test del backend (`httpx` para `TestClient`) las agrega T7 si hacen falta.

### Critical Decision — T6: `py.typed` en `model` y `# pyright: ignore[reportCallIssue]` al instanciar settings
**What:** se agrega `model/src/model/py.typed`. Las llamadas `DatabaseSettings()` / `DatabaseSettings(_env_file=None)` llevan `# pyright: ignore[reportCallIssue]` puntual (en `db.py`, `migrations/env.py` y los tests). `get_engine()` es singleton vía `functools.cache`, y `model` también reexporta `DatabaseSettings`, `missing_env_vars` y `root_env_file`.
**Why:** sin `py.typed`, Pyright strict trata el miembro editable `model` como librería sin tipos (`reportMissingTypeStubs`) en todos los imports. pydantic-settings usa `dataclass_transform`, así que Pyright exige `database_url` y no reconoce `_env_file` aunque se lean del entorno.
**Affects:** `model/src/model/py.typed`; T7 y T8 necesitan el mismo ignore puntual al instanciar `BackendSettings()` / `WorkerSettings()` (o agregar `py.typed` a `backend`/`worker` si otro paquete los importa).

### Critical Decision — T7: `app` diferido en `backend.main` vía `__getattr__` de módulo
**What:** `backend/main.py` no ejecuta `app = create_app(load_settings())` al importarse: expone `app` con un `__getattr__` de módulo que lo construye (y cachea) al pedirlo. `backend.main:app` sigue siendo el target de uvicorn.
**Why:** con el `app` a nivel de módulo, importar `create_app` (tests, `export_openapi`) exigiría `DATABASE_URL` o terminaría con `SystemExit(2)`; así `uv run python -m backend.export_openapi` funciona sin `.env`.
**Affects:** `backend/src/backend/main.py`; el `CMD` de T10 (`uvicorn backend.main:app`) y el comando dev de T14 no cambian.

### Critical Decision — T7: `httpx2` en el grupo `dev`, `py.typed` en `backend` y tests de settings sin `.env`
**What:** se agrega `httpx2` al grupo `dev` de la raíz y `backend/src/backend/py.typed`. Los tests de settings anulan el `.env` con `monkeypatch.setitem(BackendSettings.model_config, "env_file", None)`. `ping_database(engine)` queda separado de `get_db_probe` y se prueba contra `127.0.0.1:1` (puerto cerrado, sin Postgres). El orden de imports sigue la detección por defecto de Ruff (`backend`/`worker` en el bloque third-party); no se configuró `[tool.ruff] src` porque reordenaría los tests del worker (T8).
**Why:** Starlette 1.10 tipa `TestClient` con `httpx2`; sin él Pyright strict reporta los `Response` como unknown y emite un `DeprecationWarning`. Sin `py.typed`, Pyright marca `reportMissingTypeStubs` al importar `backend`.
**Affects:** `pyproject.toml`, `uv.lock`, `backend/src/backend/py.typed`, `backend/tests/*`. T13 puede unificar el orden de imports con `src = [...]` corriendo `ruff check --fix` en todo el repo.

### Critical Decision — T8: `GatewayError`, `serve()` y `main(env_file)` en el worker
**What:** `MatrizClientGateway.connect()` traduce `MatrizClientError | httpx.HTTPError` a `worker.matriz_gateway.GatewayError`, y `runner.run` solo captura esa excepción (si falla, también cierra el gateway antes de devolver `1`). El manejo de señales está en `runner.serve()`, que registra SIGINT/SIGTERM con `add_signal_handler` y los quita al terminar. `__main__.main(env_file=...)` recibe el `.env` como parámetro para que los tests lo desactiven, y si una variable es inválida (no faltante) loguea `Invalid worker configuration` con exit `2`. Se agregó `worker/src/worker/py.typed` y `asyncio_mode = "auto"` + `asyncio_default_fixture_loop_scope = "function"` en `worker/pyproject.toml`. `.env.example` ya no tiene `MATRIZ_ACCOUNT` y usa la URL de reMarkets (según T4).
**Why:** así el runner y el `FakeGateway` no dependen de los tipos de `matriz_client`, y las señales se prueban de verdad con `os.kill` sin matar a pytest. Sin `py.typed`, Pyright strict marca `reportMissingTypeStubs` en cada `import worker.*`, porque el paquete se resuelve como editable instalado.
**Affects:** `worker/src/worker/*`, `worker/tests/*`, `worker/pyproject.toml`, `.env.example`. **T13/T14:** `uv run pyright worker` (con un directorio de primer nivel como argumento) no imprime nada y sale con 0 aunque haya errores (Pyright 1.1.414). Hay que usar `uv run pyright` sin argumentos (que toma el `include` del `pyproject.toml`) o rutas a subdirectorios; T7 tiene que agregar `backend/src/backend/py.typed` por el mismo motivo.

### Critical Decision — T9: `openapi.json` fuera de Biome, `NODE_ENV=test` en Vitest y `TError` explícito
**What:** `frontend/biome.json` excluye `openapi.json`; `vite.config.ts` fija `test.env.NODE_ENV = 'test'`; `orval.config.ts` entra en `tsconfig.node.json`; `HealthPage` usa `useGetHealth<getHealthResponse, Error>()` y el mutator devuelve `{ data, status, headers }` (forma de Orval 8 con `httpClient: 'fetch'`).
**Why:** `biome format --write` reformatea el JSON y rompe la comparación byte a byte de `test_openapi_snapshot.py`; con `NODE_ENV=production` heredado del shell, React carga su build de producción sin `act` y los tests fallan; Orval 8 tipa el error como `HealthResponse`, pero `customFetch` lanza `ApiError` (o errores de red/timeout) en respuestas no-2xx.
**Affects:** `frontend/biome.json`, `frontend/vite.config.ts`, `frontend/tsconfig.node.json`, `frontend/src/pages/HealthPage.tsx`, `frontend/src/api/http.ts`. T13 (`check.sh`) puede correr `npm test` sin limpiar `NODE_ENV`; regenerar `openapi.json` siempre con `export_openapi`, nunca formatearlo a mano.

### Critical Decision — T12: `base_url` también lee `E2E_BASE_URL` del `.env` raíz
**What:** el fixture `base_url` (session, sobreescribe el de `pytest-playwright`) resuelve en orden: variable de entorno `E2E_BASE_URL`, el valor en el `.env` raíz (con un parser mínimo, sin dependencias nuevas) y por último `http://localhost:8080`.
**Why:** el plan solo usaba `os.environ.get`, pero AC-38 y AC-26 piden leer la configuración del `.env` raíz. `e2e` no depende de `pydantic-settings` ni de `python-dotenv`.
**Affects:** `e2e/tests/conftest.py`; T14 documenta que `E2E_BASE_URL` puede venir del `.env` o del entorno.

### Critical Decision — T13: `check.sh` corre todos los gates y `check-versions.sh` valida `engines.node` exacto
**What:** `scripts/check.sh` ejecuta todos los gates aunque alguno falle (`check-versions`, `ruff check`, `ruff format --check`, `pyright`, `pytest` en `model`/`backend`/`worker`, y `lint`/`format:check`/`typecheck`/`test` del frontend vía `npm --prefix frontend`), lista los que fallaron y sale con 1. `scripts/check-versions.sh` compara los tags `python:*`/`node:*` de `*/Dockerfile` (`3.13` o `3.13-*`) y exige `engines.node == ">=N <N+1"` según `.nvmrc`; ignora las demás imágenes (`nginx`). No usa `jq`. Además se reformateó `frontend/biome.json` con `biome format --write`, porque el array `includes` agregado en T9 rompía `format:check`.
**Why:** un resumen con todos los gates sirve más que cortar en el primer fallo, y sin `jq` los scripts no agregan prerrequisitos. `e2e` no entra en `check.sh` porque necesita el stack levantado (AC-36).
**Affects:** `scripts/check.sh`, `scripts/check-versions.sh`, `frontend/biome.json`; T14 documenta `scripts/check.sh` como gate local.

### Critical Decision — T14: `npm ci --include=dev` como comando de setup documentado
**What:** README y los `CLAUDE.md` documentan `npm ci --include=dev` en lugar de `npm ci`, y el README advierte que el worker sale con 1 (y en Compose queda `exited`) con las credenciales `changeme` del ejemplo. Los comandos se verificaron sobre una copia limpia del repo en `/tmp` (`uv sync`, `npm ci`, `scripts/check.sh`, comandos dev, Alembic, `docker compose up --build`, `uv run pytest e2e`).
**Why:** en el entorno de verificación `NODE_ENV=production` estaba exportado y `npm ci` omitía las devDependencies, así que lint/test/build del frontend fallaban con `biome`/`orval: command not found`. `--include=dev` funciona igual con o sin esa variable.
**Affects:** `README.md`, `CLAUDE.md`, `frontend/CLAUDE.md`. El `frontend/Dockerfile` no cambia.
