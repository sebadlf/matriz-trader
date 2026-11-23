# Plan: Bases del proyecto matriz-trader (setup inicial)

> Esqueleto de monorepo `backend/` (Python 3.13 + FastAPI + uv) y `frontend/` (React + TS + Vite+ + Orval), con PostgreSQL, dos archivos de Docker Compose (dev/prod), un único `.env` raíz y `CLAUDE.md`/`README.md`, todas las herramientas de calidad en verde sin lógica de negocio. Appetite: M. Risk: medium.

## Approach

```mermaid
flowchart LR
  A["Raíz: .gitignore + .env.example"] --> B["backend/: uv + FastAPI + GET /api/health"]
  B --> C["backend/openapi.json exportado y versionado"]
  C --> D["frontend/: Orval react-query + mutator fetch"]
  D --> E["Docker Compose dev y prod + nginx"]
  E --> F["CLAUDE.md + README.md verificados en clon limpio"]
```

Construimos de adentro hacia afuera. Primero va la configuración raíz y la de cada módulo (lint, tipos y tests en verde sobre código mínimo). Después el backend expone un único `GET /api/health` y vuelca su OpenAPI a `backend/openapi.json`, que queda versionado. Orval genera desde ese archivo el cliente react-query que consume la única pantalla del frontend. Por último, cada módulo tiene un `Dockerfile` multi-stage, hay dos compose independientes y la documentación se valida ejecutando el README sobre un clon limpio. Alternativas descartadas: un solo `docker-compose.yml` con overrides, porque Resolved Decisions eligió dos archivos completos; que Orval lea el OpenAPI de un backend en ejecución, porque se pierde reproducibilidad y AC-24 se vuelve frágil; y servir el build con FastAPI o `vp preview`, porque contradice AC-31 y AC-30 (Resolved Decisions). También descarto Alembic en esta etapa (Resolved Decisions).

## Affected files

El repositorio no tiene commits. Todos los archivos son nuevos salvo `future-plans/frontend-quality-prompt.md`, que existe y se usa como fuente de las convenciones del frontend en `CLAUDE.md`.

| File | Change |
|---|---|
| `./.gitignore` | Nuevo. Ignora `.env`, `.venv/`, `__pycache__/`, `node_modules/`, `dist/`, `playwright-report/` y `test-results/`; re-incluye `!.env.example` (AC-1, AC-2) |
| `./.env.example` | Nuevo. Todas las variables con valor de ejemplo y comentario (AC-4) |
| `./docker-compose.dev.yml` | Nuevo. Servicios `db`, `backend` (target `dev`) y `frontend` (target `dev`) (AC-29, AC-31, AC-32, AC-33) |
| `./docker-compose.prod.yml` | Nuevo. Servicios `db`, `backend` (target `prod`) y `frontend` (nginx) (AC-30, AC-31, AC-32, AC-33) |
| `./CLAUDE.md` | Nuevo (AC-35, NFR-6) |
| `./README.md` | Nuevo (AC-7, AC-10, AC-34, AC-36, AC-37) |
| `future-plans/frontend-quality-prompt.md:1` | Solo lectura. Sus secciones 2 a 14 se condensan en `CLAUDE.md` (AC-35) |
| `backend/pyproject.toml` | Nuevo. Dependencias, `tool.uv.sources` por tag, Ruff, mypy y pytest (AC-5, AC-12, AC-13, AC-15, NFR-1, NFR-5) |
| `backend/uv.lock` | Nuevo y versionado (NFR-1, NFR-2) |
| `backend/.python-version` | Nuevo, contiene `3.13` (AC-5) |
| `backend/.dockerignore` | Nuevo. Excluye `.venv`, `.env`, `__pycache__`, `.mypy_cache` y `.ruff_cache` (NFR-3) |
| `backend/Dockerfile` | Nuevo. Targets `base`, `dev`, `builder` y `prod`, con `RUN --mount=type=ssh` (AC-29, AC-30, AC-34) |
| `backend/app/__init__.py` | Nuevo. `__version__ = "0.1.0"` |
| `backend/app/__main__.py` | Nuevo. Entrypoint `python -m app [--reload]` (AC-8, AC-9) |
| `backend/app/core/config.py` | Nuevo. `Settings`, `load_settings()` y `get_settings()` (AC-8, AC-9) |
| `backend/app/db/base.py` | Nuevo. `Base(DeclarativeBase)` y `TimestampMixin` (AC-11, AC-16) |
| `backend/app/db/session.py` | Nuevo. Engine async y `async_sessionmaker` (AC-11) |
| `backend/app/api/router.py` | Nuevo. `api_router` con prefijo `/api` |
| `backend/app/api/routes/health.py` | Nuevo. `GET /api/health` |
| `backend/app/schemas/health.py` | Nuevo. `HealthResponse` |
| `backend/app/main.py` | Nuevo. `create_app()`, `lifespan` y `app` (AC-10) |
| `backend/app/scripts/export_openapi.py` | Nuevo. Escribe `backend/openapi.json` |
| `backend/openapi.json` | Nuevo, generado y versionado. Es el input de Orval |
| `backend/tests/conftest.py` | Nuevo. Fixture `client: AsyncClient` y env de test |
| `backend/tests/test_health.py` | Nuevo (AC-10) |
| `backend/tests/test_config.py` | Nuevo (AC-8, AC-9) |
| `backend/tests/test_db.py` | Nuevo (AC-11, AC-16) |
| `backend/tests/test_openapi_export.py` | Nuevo. Detecta drift entre `openapi.json` y `app.openapi()` |
| `backend/tests/test_tooling.py` | Nuevo. Verifica imports de las libs y la regla ANN (AC-6, AC-13, AC-14) |
| `frontend/package.json` | Nuevo. Dependencias y scripts `generate:api` y `e2e` (AC-18) |
| `frontend/pnpm-lock.yaml` | Nuevo y versionado (NFR-2) |
| `frontend/vite.config.ts` | Nuevo. Config de Vite, lint, fmt, test, alias `@/`, `envDir: '..'` y proxy `/api` (AC-3, NFR-4, NFR-6) |
| `frontend/tsconfig.json` | Nuevo. `strict` y `paths` `@/*` (AC-22) |
| `frontend/tsconfig.node.json` | Nuevo. Para `vite.config.ts`, `orval.config.ts` y `playwright.config.ts` |
| `frontend/index.html` | Nuevo |
| `frontend/orval.config.ts` | Nuevo. Input `../backend/openapi.json` (AC-23, AC-24) |
| `frontend/playwright.config.ts` | Nuevo (AC-28) |
| `frontend/e2e/home.spec.ts` | Nuevo (AC-28) |
| `frontend/Dockerfile` | Nuevo. Targets `dev`, `build` y `prod` (nginx) (AC-29, AC-30) |
| `frontend/nginx.conf` | Nuevo. SPA fallback y proxy `/api/` → `backend:8000` (AC-30, AC-31) |
| `frontend/.dockerignore` | Nuevo (NFR-3) |
| `frontend/src/main.tsx` | Nuevo. Monta `<AppProviders><AppRouter/></AppProviders>` |
| `frontend/src/vite-env.d.ts` | Nuevo |
| `frontend/src/app/providers.tsx` | Nuevo. `ConfigProvider`, `App` de AntD y `QueryClientProvider` (AC-20) |
| `frontend/src/app/router.tsx` | Nuevo. `createBrowserRouter`, ruta index lazy y `*` → 404 (AC-20, AC-21) |
| `frontend/src/app/theme.ts` | Nuevo. `ThemeConfig` base |
| `frontend/src/api/mutator.ts` | Nuevo. Único punto con `fetch` (AC-23, AC-25) |
| `frontend/src/api/queryClient.ts` | Nuevo. `createQueryClient()` |
| `frontend/src/api/generated/health/health.ts` | Nuevo, generado por Orval (AC-23) |
| `frontend/src/api/generated/model/*.ts` | Nuevo, generado por Orval (AC-23) |
| `frontend/src/screens/HomeScreen/HomeScreen.tsx` | Nuevo. Consume `useGetHealth()` |
| `frontend/src/screens/HomeScreen/HomeScreen.test.tsx` | Nuevo (AC-27) |
| `frontend/src/screens/HomeScreen/index.ts` | Nuevo |
| `frontend/src/screens/NotFoundScreen/NotFoundScreen.tsx` | Nuevo. `Result status="404"` (AC-21) |
| `frontend/src/screens/NotFoundScreen/NotFoundScreen.test.tsx` | Nuevo (AC-21, AC-27) |
| `frontend/src/screens/NotFoundScreen/index.ts` | Nuevo |
| `frontend/src/layouts/RootLayout.tsx` | Nuevo. `Layout` de AntD con `<Outlet/>` |
| `frontend/src/constants/routes.ts` | Nuevo. `ROUTES` |
| `frontend/src/test/setup.ts` | Nuevo. jest-dom y polyfill de `matchMedia` |
| `frontend/src/test/render.tsx` | Nuevo. `renderWithProviders()` (AC-27) |
| `frontend/src/{components,hooks,stores,utils,types}/.gitkeep` | Nuevo. Directorios vacíos versionados (AC-19) |

## Backend changes

**`backend/pyproject.toml`** (el proyecto no se empaqueta y se ejecuta desde `backend/`):

```toml
[project]
name = "matriz-trader-backend"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "sqlalchemy[asyncio]>=2.0.36,<2.1",
  "psycopg[binary]>=3.2",
  "pydantic>=2.9",
  "pydantic-settings>=2.6",
  "market-data-client",
  "matriz-client",
]

[dependency-groups]
dev = ["ruff>=0.8", "mypy>=1.13", "pytest>=8.3", "pytest-asyncio>=0.24", "httpx>=0.27"]

[tool.uv]
package = false

[tool.uv.sources]
market-data-client = { git = "ssh://git@github.com/gravity-quant/market-libs.git", tag = "market-data-client-v0.7.1", subdirectory = "packages/market-data-client" }
matriz-client      = { git = "ssh://git@github.com/gravity-quant/market-libs.git", tag = "matriz-client-v0.4.0",      subdirectory = "packages/matriz-client" }

[tool.ruff]
target-version = "py313"
line-length = 100
extend-exclude = ["openapi.json"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "N", "SIM", "RUF", "ANN"]
# Sin ignore ni per-file-ignores de reglas ANN (AC-13): los tests también se anotan.

[tool.mypy]
python_version = "3.13"
strict = true
plugins = ["pydantic.mypy"]          # sin "sqlalchemy.ext.mypy.plugin" (AC-15)
exclude = ["^\\.venv/"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

Verifiqué el repo `gravity-quant/market-libs`: los tags `market-data-client-v0.7.1` y `matriz-client-v0.4.0` existen, los paquetes están en `packages/<name>` y exponen los módulos `market_data_client` y `matriz_client`. Los dos incluyen `py.typed`, así que mypy strict no necesita `ignore_missing_imports` (AC-5, AC-6).

**Settings** en `backend/app/core/config.py` (AC-8, AC-9):

```python
ROOT_ENV_FILE: Final = Path(__file__).resolve().parents[3] / ".env"   # <repo>/.env

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )
    app_env: Literal["development", "production"] = "development"
    database_url: PostgresDsn                      # obligatoria, sin default
    backend_host: str = "0.0.0.0"
    backend_port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["critical", "error", "warning", "info", "debug"] = "info"

def load_settings() -> Settings: ...   # ValidationError -> stderr "Configuración inválida: DATABASE_URL (...)" + SystemExit(1)

@lru_cache
def get_settings() -> Settings: ...    # return load_settings()
```

**Entrypoint** `backend/app/__main__.py`:

```python
def main(argv: Sequence[str] | None = None) -> None:
    # argparse: --reload (flag)
    settings = load_settings()           # valida antes de levantar uvicorn (AC-9)
    uvicorn.run("app.main:app", host=settings.backend_host, port=settings.backend_port,
                reload=args.reload, reload_dirs=["app"], log_level=settings.log_level)
```

**Capa de DB** en `backend/app/db/base.py` y `backend/app/db/session.py` (AC-11, AC-16), sin modelos de negocio:

```python
NAMING_CONVENTION: Final = {
    "ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

def build_engine(database_url: str) -> AsyncEngine: ...          # create_async_engine(url, pool_pre_ping=True)
def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]: ...  # expire_on_commit=False
async def get_session(request: Request) -> AsyncIterator[AsyncSession]: ...  # usa request.app.state.session_factory
```

**API** en `backend/app/schemas/health.py`, `backend/app/api/routes/health.py` y `backend/app/main.py` (AC-10):

```python
class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["matriz-trader-backend"]
    version: str

@router.get("/health", operation_id="getHealth", tags=["health"], response_model=HealthResponse)
async def get_health() -> HealthResponse: ...        # no toca la DB

def create_app() -> FastAPI:
    # FastAPI(title="matriz-trader API", version=__version__, lifespan=lifespan,
    #         openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url=None)
    # include_router(api_router)  # api_router = APIRouter(prefix="/api")
    ...

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # settings = get_settings(); engine = build_engine(str(settings.database_url))
    # app.state.session_factory = build_session_factory(engine); yield; await engine.dispose()
    ...

app = create_app()   # create_app() no lee Settings: export_openapi funciona sin .env ni DB
```

**Export del OpenAPI** en `backend/app/scripts/export_openapi.py` (Resolved Decisions):

```python
OUTPUT: Final = Path(__file__).resolve().parents[2] / "openapi.json"   # backend/openapi.json
def main() -> None:  # OUTPUT.write_text(json.dumps(create_app().openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n")
```

## Frontend changes

**`frontend/package.json`** (AC-18): no se agrega ningún cliente HTTP ni gestor de estado ni librería de UI distintos de los listados, ni tampoco ESLint, Prettier o Jest.

```jsonc
{
  "name": "matriz-trader-frontend",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@<versión fijada en T3>",
  "scripts": {
    "generate:api": "orval --config orval.config.ts",
    "e2e": "playwright test"
  },
  "dependencies": {
    "react": "^19", "react-dom": "^19", "antd": "^5", "react-router": "^7",
    "zustand": "^5", "@tanstack/react-query": "^5"
  },
  "devDependencies": {
    "typescript": "^5", "vite-plus": "<latest>", "@vitejs/plugin-react": "<latest>", "orval": "^7",
    "@playwright/test": "^1", "@testing-library/react": "^16", "@testing-library/user-event": "^14",
    "@testing-library/jest-dom": "^6", "jsdom": "<latest>", "@types/react": "^19", "@types/react-dom": "^19"
  }
}
```

**`frontend/vite.config.ts`**, la única config de lint, fmt y test (NFR-4). Las claves `lint`, `fmt` y `test` siguen el esquema de Vite+ y se verifican en T3:

```ts
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '');                       // lee <repo>/.env y process.env (AC-3)
  return {
    envDir: '..',
    plugins: [react()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: { host: true, port: 5173, proxy: { '/api': { target: env.BACKEND_URL ?? 'http://localhost:8000', changeOrigin: true } } },
    lint: { ignorePatterns: ['src/api/generated/**', 'dist/**'] },   // NFR-6
    fmt:  { ignorePatterns: ['src/api/generated/**', 'dist/**', 'pnpm-lock.yaml'] },
    test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], include: ['src/**/*.test.{ts,tsx}'], css: false },
  };
});
```

**`frontend/tsconfig.json`** (AC-22):

```jsonc
{ "compilerOptions": { "target": "ES2022", "module": "ESNext", "moduleResolution": "bundler", "jsx": "react-jsx",
  "strict": true, "noUncheckedIndexedAccess": true, "noImplicitOverride": true, "noEmit": true,
  "baseUrl": ".", "paths": { "@/*": ["src/*"] }, "types": ["vite/client", "@testing-library/jest-dom"] },
  "include": ["src"], "references": [{ "path": "./tsconfig.node.json" }] }
```

**Orval** en `frontend/orval.config.ts` (AC-23, AC-24):

```ts
export default defineConfig({
  matrizTrader: {
    input: { target: '../backend/openapi.json' },
    output: {
      mode: 'tags-split', client: 'react-query', httpClient: 'fetch',
      target: 'src/api/generated', schemas: 'src/api/generated/model', clean: true, prettier: false,
      override: { mutator: { path: 'src/api/mutator.ts', name: 'customFetch' } },
    },
  },
});
```

**Mutator** en `frontend/src/api/mutator.ts`, el único archivo de `src/` con `fetch(` (AC-25):

```ts
export class ApiError<TBody = unknown> extends Error {
  constructor(public readonly status: number, public readonly body: TBody) { super(`HTTP ${status}`); }
}
export type ErrorType<TBody> = ApiError<TBody>;          // lo usa Orval para tipar errores
const BASE_URL = '';                                       // mismo origen: proxy de Vite (dev) o nginx (prod)
export const customFetch = async <T>(url: string, init?: RequestInit): Promise<T> => { ... };
// !res.ok -> throw new ApiError(res.status, body). Si no, devuelve el shape que espera Orval
// para httpClient 'fetch' (ajustar en T8 al tipo de respuesta generado, sin casts `as` injustificados).
```

**App shell** (AC-20, AC-21):

```ts
// constants/routes.ts
export const ROUTES = { home: '/', notFound: '*' } as const;

// app/providers.tsx
type AppProvidersProps = { children: ReactNode; queryClient?: QueryClient };
// <ConfigProvider theme={theme}><AntdApp><QueryClientProvider client={qc}>{children}</QueryClientProvider></AntdApp></ConfigProvider>

// app/router.tsx
export const routes: RouteObject[] = [{
  path: ROUTES.home, element: <RootLayout />, errorElement: <NotFoundScreen />,
  children: [
    { index: true, lazy: async () => ({ Component: (await import('@/screens/HomeScreen')).HomeScreen }) },
    { path: ROUTES.notFound, element: <NotFoundScreen /> },
  ],
}];
export const AppRouter = () => <RouterProvider router={createBrowserRouter(routes)} />;

// api/queryClient.ts
export const createQueryClient = (overrides?: QueryClientConfig): QueryClient => ...; // staleTime 30_000, retry 1

// test/render.tsx (AC-27)
export function renderWithProviders(ui: ReactElement, opts?: { route?: string }):
  RenderResult & { user: UserEvent };   // QueryClient nuevo con retry:false, MemoryRouter en opts.route
```

`HomeScreen` usa `useGetHealth()`. Con `isPending` muestra `<Spin/>`, con `isError` un `<Alert type="error"/>` y con éxito `<Result status="success" title="matriz-trader" subTitle={`Backend: ${data.status}`}/>`. `NotFoundScreen` usa `<Result status="404" title="404" subTitle="Página no encontrada" extra={<Link to={ROUTES.home}>Volver al inicio</Link>}/>`.

**Playwright** en `frontend/playwright.config.ts` y `frontend/e2e/home.spec.ts` (AC-28):

```ts
// playwright.config.ts
export default defineConfig({ testDir: './e2e', use: { baseURL: 'http://localhost:5173' },
  projects: [{ name: 'chromium', use: devices['Desktop Chrome'] }],
  webServer: { command: 'vp dev --port 5173 --strictPort', url: 'http://localhost:5173', reuseExistingServer: !process.env.CI } });
// home.spec.ts: page.route('**/api/health', fulfill {status:'ok',service:'matriz-trader-backend',version:'0.1.0'})
//   -> goto('/') -> expect(getByText('Backend: ok')).toBeVisible()
//   -> goto('/no-existe') -> expect(getByText('404')).toBeVisible()
```

## Infra (Docker Compose) changes

**`./.env.example`**: lista todas las variables que usan el backend, el frontend y compose (AC-4). Cada una lleva un comentario `#` en la línea anterior:

```dotenv
# --- PostgreSQL (lo usan los servicios db de compose) ---
POSTGRES_USER=matriz
POSTGRES_PASSWORD=change-me-local-only
POSTGRES_DB=matriz_trader
POSTGRES_PORT=5432
# --- Backend (Settings de Pydantic) ---
APP_ENV=development
DATABASE_URL=postgresql+psycopg://matriz:change-me-local-only@localhost:5432/matriz_trader
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
LOG_LEVEL=info
# --- Frontend (vite.config.ts, sin prefijo VITE_: no llega al bundle) ---
BACKEND_URL=http://localhost:8000
FRONTEND_PORT=5173
FRONTEND_PROD_PORT=8080
```

**`backend/Dockerfile`** (AC-29, AC-30, AC-34). La clave SSH solo se usa durante el build mediante `--mount=type=ssh` y nunca queda en una capa:

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client && rm -rf /var/lib/apt/lists/* \
 && mkdir -p -m 0700 /root/.ssh && ssh-keyscan github.com >> /root/.ssh/known_hosts
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./

FROM base AS dev
RUN --mount=type=ssh uv sync --frozen
COPY app ./app
CMD ["python", "-m", "app", "--reload"]

FROM base AS builder
RUN --mount=type=ssh uv sync --frozen --no-dev
COPY app ./app

FROM python:3.13-slim AS prod
ENV PATH=/opt/venv/bin:$PATH
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/app ./app
USER app
CMD ["python", "-m", "app"]
```

**`frontend/Dockerfile`**: el target `dev` parte de `node:22-slim` con Vite+ y pnpm, y ejecuta `CMD vp dev --host 0.0.0.0 --port 5173`. El target `build` corre `vp install --frozen-lockfile && vp build`. El target `prod` es `nginxinc/nginx-unprivileged:1.27-alpine`, copia `dist/` a `/usr/share/nginx/html` y usa `nginx.conf`. La imagen final no lleva Node ni dependencias de desarrollo (AC-30).

**`frontend/nginx.conf`**: el upstream se resuelve de forma lazy, así nginx arranca aunque el backend no esté levantado (AC-31):

```nginx
server {
  listen 8080;
  root /usr/share/nginx/html;
  location /api/ {
    resolver 127.0.0.11 valid=10s ipv6=off;
    set $backend_upstream http://backend:8000;
    proxy_pass $backend_upstream;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
  location / { try_files $uri $uri/ /index.html; }
}
```

**`docker-compose.dev.yml`**: `docker-compose.prod.yml` tiene la misma forma con `name: matriz-trader-prod`, target `prod`, sin bind mounts ni `--reload`, y el frontend publicado en `${FRONTEND_PROD_PORT:-8080}:8080` (AC-29 a AC-33):

```yaml
name: matriz-trader-dev
x-env: &root-env
  env_file: [{ path: .env, required: false }]   # el guard :? de abajo da el mensaje (AC-33)
services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?Falta .env en la raíz. Ejecutá cp .env.example .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Falta .env en la raíz. Ejecutá cp .env.example .env}
      POSTGRES_DB: ${POSTGRES_DB:?Falta .env en la raíz. Ejecutá cp .env.example .env}
    ports: ["${POSTGRES_PORT:-5432}:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"], interval: 5s, retries: 10 }
  backend:
    <<: *root-env
    build: { context: ./backend, target: dev, ssh: [default] }
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      BACKEND_HOST: 0.0.0.0
      BACKEND_PORT: "8000"
    volumes: [./backend/app:/app/app]
    ports: ["${BACKEND_PORT:-8000}:8000"]
    depends_on: { db: { condition: service_healthy } }
  frontend:
    <<: *root-env
    build: { context: ./frontend, target: dev }
    environment: { BACKEND_URL: http://backend:8000 }
    volumes: [./frontend:/app, /app/node_modules]
    ports: ["${FRONTEND_PORT:-5173}:5173"]
    # sin depends_on: `up frontend` no levanta el backend (AC-31)
volumes:
  pgdata: {}   # volumen con nombre: matriz-trader-dev_pgdata (AC-32)
```

## Docs changes

- `CLAUDE.md` (AC-35, NFR-6) tiene estas secciones:
  - Stack por módulo.
  - Estructura de carpetas: el árbol de `backend/app` y el de `frontend/src`.
  - Reglas de dependencia del frontend (§4 del prompt de calidad).
  - Comandos de dev, calidad y tests por módulo.
  - Flujo Orval en cuatro pasos: (1) cambiar endpoints, (2) `uv run python -m app.scripts.export_openapi`, (3) `vp run generate:api`, (4) commitear `backend/openapi.json` y `frontend/src/api/generated/`.
  - Regla "el frontend solo habla con el backend vía Orval; `fetch` solo en `src/api/mutator.ts`".
  - `src/api/generated/` no se edita a mano.
  - Convenciones del backend: `Mapped[...]`, ANN sin excepciones, mypy strict sin plugin de SQLAlchemy, `operation_id` explícito en cada ruta.
  - Definición de "terminado" por módulo.
- `README.md` (AC-7, AC-10, AC-34, AC-36, AC-37) tiene estas secciones, en este orden:
  - Descripción.
  - Prerrequisitos: Python 3.13, uv ≥ 0.9, Node 22 + Vite+ + pnpm, Docker con Compose ≥ 2.24 y acceso SSH a `gravity-quant/market-libs` con `ssh -T git@github.com`.
  - Configuración: `cp .env.example .env`.
  - Backend local, con la URL `http://localhost:8000/api/openapi.json` y `/api/docs`.
  - Frontend local.
  - Docker Compose dev y prod: `ssh-add` + `docker compose -f docker-compose.<modo>.yml up -d --build [servicio]`, con la nota de `--ssh default` para `docker build` directo.
  - Calidad y tests.
  - Troubleshooting de SSH.

## Key implementation details

- **Un solo `.env`** (AC-3): el backend lo lee con `ROOT_ENV_FILE` y el frontend con `envDir: '..'`/`loadEnv('..')`. Compose lo usa para interpolar y como `env_file`. Dentro de los contenedores no existe ningún `.env`: las variables llegan por el entorno, y pydantic-settings ignora un `env_file` inexistente. Ningún `.dockerignore` deja pasar `.env`.
- **Arranque del backend** (AC-9): solo `python -m app` valida Settings y termina con `exit 1` y el mensaje `Configuración inválida: <VAR>[, <VAR>]`, seguido del detalle de Pydantic. Los nombres se toman de `exc.errors()[i]["loc"][0]` en mayúsculas. `create_app()` no lee Settings, así que importar `app.main` (tests y export) no requiere `.env`. Si se arranca con `uvicorn app.main:app` y falta configuración, falla igual en el `lifespan`, pero el comando documentado es `python -m app`.
- **Tests del backend**: `conftest.py` usa `monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/test")` y un fixture `client` con `httpx.AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")`. `ASGITransport` no ejecuta el lifespan, así que no hace falta DB.
  - `test_config.py` ejecuta `subprocess.run([sys.executable, "-m", "app"], cwd=backend, env=...)` en dos casos: `DATABASE_URL=""` y `BACKEND_PORT=abc`. En ambos verifica `returncode != 0` y que stderr nombre la variable. Usa valores inválidos explícitos, porque las variables de entorno tienen prioridad sobre el `.env` raíz y así el test no depende de que ese archivo exista. La carga desde archivo (AC-8) se prueba con `Settings(_env_file=tmp_path / ".env")`.
  - `test_tooling.py` ejecuta `import market_data_client, matriz_client` (AC-6) y `subprocess` `ruff check --stdin-filename probe.py -` con `def f(x): return x`. Espera `ANN001` y `ANN201` en la salida (AC-14). También parsea `pyproject.toml` con `tomllib` para confirmar que `"ANN"` está en `select` y que no hay `ANN*` en `ignore`/`per-file-ignores` (AC-13).
  - `test_openapi_export.py` compara `json.loads(openapi.json)` con `create_app().openapi()` para que un export olvidado rompa CI local.
- **Formato de `openapi.json`**: `indent=2`, `sort_keys=True`, newline final. Ruff no lo procesa.
- **Orval**: el `operation_id="getHealth"` explícito garantiza los nombres estables `getHealth`/`useGetHealth`/`getGetHealthQueryKey`. Con `mode: 'tags-split'` la salida queda en `src/api/generated/health/health.ts`. `clean: true` borra la salida anterior. Hay que confirmar en T8 que, si `../backend/openapi.json` no existe, Orval sale con código ≠ 0 y nombra la ruta (AC-24). Si no la nombra, `generate:api` pasa a ser `node -e "fs.accessSync('../backend/openapi.json')" && orval ...`, y Node muestra la ruta en el `ENOENT`. Ese cambio se registra en Critical Decisions.
- **Directorios vacíos** (AC-19): `components/`, `hooks/`, `stores/`, `utils/` y `types/` llevan `.gitkeep`. `app/`, `api/`, `screens/`, `layouts/`, `constants/` y `test/` tienen contenido real.
- **Tests del frontend**: `src/test/setup.ts` importa `@testing-library/jest-dom/vitest` y define `window.matchMedia`, que AntD necesita en jsdom. `HomeScreen.test.tsx` usa un `QueryClient` precargado con `setQueryData(getGetHealthQueryKey(), …)`. No usa MSW, para no sumar dependencias: los mocks MSW de Orval (`mock: true`) quedan para cuando haya más endpoints. `NotFoundScreen.test.tsx` renderiza `routes` en un `createMemoryRouter` con `initialEntries: ['/no-existe']` y espera `getByText('404')` (AC-21, AC-27).
- **AC-25**: además del grep de verificación, el único `fetch(` del árbol vive en `src/api/mutator.ts`. `CLAUDE.md` documenta la regla.
- **Compose**: `name:` distinto por archivo, para que dev y prod no compartan contenedores ni volumen. `docker compose -f docker-compose.dev.yml up backend` levanta `db` + `backend` por `depends_on`, y `up frontend` levanta solo `frontend` (AC-31). En el frontend dev, el `node_modules` del contenedor queda en un volumen anónimo para no pisar el del host.
- **SSH en el build** (AC-34): compose pasa `ssh: [default]` y requiere `ssh-agent` con la clave cargada (`ssh-add`). Si no está, `uv sync` falla con `Permission denied (publickey)` y exit ≠ 0. La imagen `prod` parte de `python:3.13-slim` limpia, sin git, ssh ni known_hosts.
- **Puertos**: el backend usa 8000, Vite dev 5173, nginx prod 8080 y Postgres 5432. Todos son configurables en el host vía `.env`.

## Risks & rollback

| Risk | Mitigation | How to revert |
|---|---|---|
| La API de Vite+ (`vite-plus`, claves `lint`/`fmt`/`test` en `defineConfig`, `vp install`) difiere de lo asumido; no se pudo verificar online al planificar | T3 instala Vite+ según su documentación oficial y ajusta solo `frontend/vite.config.ts`/`package.json`; cualquier desvío se registra en Critical Decisions | Revertir el commit de T3; los demás módulos no dependen de esas claves |
| Orval con `httpClient: 'fetch'` + mutator espera un shape de respuesta específico (`{ data, status, headers }`) | T8 ajusta `customFetch` al tipo generado y `vp check` (tsc) lo valida | Cambiar `httpClient` en `orval.config.ts` y regenerar |
| El build Docker del backend falla en máquinas sin `ssh-agent` | README documenta `eval $(ssh-agent) && ssh-add`; el error es explícito (AC-34) | N/A (requisito documentado) |
| Hot reload en bind mounts de Docker Desktop (macOS) no detecta cambios | Si falla, se agrega `server.watch.usePolling` condicionado a `CHOKIDAR_USEPOLLING` y `WATCHFILES_FORCE_POLLING=true` en el backend (variables nuevas → `.env.example`) | Quitar las variables de polling |
| `test_config.py` se contamina con el `.env` real del desarrollador | Los subprocess fuerzan valores inválidos explícitos y no dependen de su ausencia | Ajustar el fixture |
| El e2e con `page.route` no prueba el backend real | Es lo decidido para que el e2e no dependa de PostgreSQL; queda en Open Questions | Agregar un segundo proyecto de Playwright contra compose |
| nginx falla al arrancar sin backend | `resolver` + variable en `proxy_pass` (resolución lazy) | Volver a `proxy_pass http://backend:8000` estático y agregar `depends_on` |

## Verification

| AC | Cómo se prueba |
|---|---|
| AC-1 | `ls -a` en la raíz muestra `backend/ frontend/ docker-compose.dev.yml docker-compose.prod.yml CLAUDE.md README.md .gitignore .env.example` (T14) |
| AC-2 | `cp .env.example .env && git check-ignore .env` imprime `.env` y sale con exit 0 |
| AC-3 | `git ls-files -co --exclude-standard '*.env' '**/.env'` vacío y `find . -name .env -not -path ./.env -not -path '*/node_modules/*'` vacío; revisión de `config.py` (`ROOT_ENV_FILE`), `vite.config.ts` (`envDir: '..'`) y compose |
| AC-4 | `rg -o '[A-Z_]{3,}' ` sobre `config.py`, `vite.config.ts`, `docker-compose.*.yml`, comparado con las claves de `.env.example`; cada clave tiene comentario |
| AC-5 | `cd backend && uv sync` sale con exit 0; `uv run python -V` es 3.13.x; `uv.lock` contiene `tag=market-data-client-v0.7.1` y `tag=matriz-client-v0.4.0` |
| AC-6 | `uv run python -c "import market_data_client, matriz_client"` sale con exit 0, y `tests/test_tooling.py` lo cubre |
| AC-7 | Con `GIT_SSH_COMMAND="ssh -i /dev/null -o IdentitiesOnly=yes"` y `uv cache clean`, `uv sync` sale con exit ≠ 0; README, sección Instalación |
| AC-8 | `tests/test_config.py`: `Settings` toma `DATABASE_URL` del entorno o archivo; revisión de `ROOT_ENV_FILE` |
| AC-9 | `tests/test_config.py`: subprocess `python -m app` sin `DATABASE_URL` o con `BACKEND_PORT=abc` → exit ≠ 0 y stderr nombra la variable |
| AC-10 | `tests/test_health.py` (`GET /api/openapi.json` 200 y `GET /api/health` 200 `{"status":"ok",...}`); README documenta la URL |
| AC-11 | `tests/test_db.py`: `Base.metadata.tables == {}`, `build_engine(url).url.drivername == "postgresql+psycopg"` y `build_session_factory` devuelve `async_sessionmaker` |
| AC-12 | `uv run ruff check . && uv run ruff format --check .` salen con exit 0 |
| AC-13 | `tests/test_tooling.py` parsea `pyproject.toml` |
| AC-14 | `tests/test_tooling.py` (probe por stdin → `ANN001`, `ANN201`) |
| AC-15 | `uv run mypy .` sale con exit 0; `pyproject.toml` tiene `strict = true` y `plugins = ["pydantic.mypy"]` |
| AC-16 | `tests/test_db.py` inspecciona `TimestampMixin.__annotations__` (`Mapped[datetime]`); `rg "Column\(" backend/app` vacío |
| AC-17 | `cd frontend && vp install && vp build` salen con exit 0 |
| AC-18 | `jq '.dependencies + .devDependencies | keys' package.json` incluye las requeridas y no incluye `eslint*`, `prettier`, `jest`, `axios`, `ky`, `redux*`, `jotai`, `mobx`, `@mui/*`, etc. |
| AC-19 | `ls frontend/src` lista los 11 directorios |
| AC-20 | Revisión de `providers.tsx`; `HomeScreen.test.tsx` renderiza con los providers; `e2e/home.spec.ts` muestra la pantalla |
| AC-21 | `NotFoundScreen.test.tsx` y el paso `/no-existe` de `e2e/home.spec.ts` |
| AC-22 | `tsconfig.json` con `strict: true` y `paths["@/*"] = ["src/*"]`; `vp build` resuelve los imports `@/` |
| AC-23 | `vp run generate:api` sale con exit 0; `git diff --exit-code src/api/generated` sin cambios tras regenerar; `orval.config.ts` tiene `client: 'react-query'` y `mutator` |
| AC-24 | `mv ../backend/openapi.json /tmp/ && vp run generate:api` → exit ≠ 0 y el mensaje contiene `backend/openapi.json`; luego se restaura el archivo |
| AC-25 | `rg -n "fetch\(|axios" frontend/src --glob '!api/**'` sin resultados |
| AC-26 | `vp lint && vp fmt --check` salen con exit 0 |
| AC-27 | `vp test run` sale con exit 0, con `HomeScreen.test.tsx` y `NotFoundScreen.test.tsx` usando `src/test/render.tsx` |
| AC-28 | `vp exec playwright install chromium && vp run e2e` sale con exit 0 |
| AC-29 | `docker compose -f docker-compose.dev.yml up -d --build`; editar `backend/app/api/routes/health.py` → log de reload de uvicorn; editar `HomeScreen.tsx` → HMR en el navegador |
| AC-30 | `docker compose -f docker-compose.prod.yml up -d --build`; `curl localhost:8080/` sirve HTML y `curl localhost:8080/api/health` devuelve 200; `docker run --rm <backend-prod> sh -c 'command -v git; ls /root/.ssh'` falla; la imagen del frontend no tiene `node` |
| AC-31 | `docker compose -f docker-compose.<modo>.yml up -d backend` → `ps` muestra `db` y `backend`; con `up -d frontend` en un proyecto limpio → `ps` muestra solo `frontend` y nginx responde en `/` |
| AC-32 | `docker volume ls` muestra `matriz-trader-dev_pgdata`; los datos sobreviven a `down` y `up` |
| AC-33 | `mv .env /tmp && docker compose -f docker-compose.dev.yml config` → exit ≠ 0 con "Falta .env en la raíz. Ejecutá cp .env.example .env" |
| AC-34 | `ssh-add -D && docker compose -f docker-compose.prod.yml build backend --no-cache` → exit ≠ 0; `docker history` sin claves; README documenta `--ssh default` |
| AC-35 | Checklist de las secciones de `CLAUDE.md` (Docs changes) |
| AC-36 | Checklist de las secciones de `README.md` (Docs changes) |
| AC-37 | T14: `git clone` a un tmpdir y ejecución de cada bloque de código del README en orden; todos salen con exit 0 |
| NFR-7 | T14 mide con `time` cada comando de AC-12, AC-15, AC-26 y AC-27 (< 60 s) |

## Tasks

### Wave 1
- [ ] T1: Crear `.gitignore` y `.env.example` en la raíz con todas las variables comentadas — _outcome: `git check-ignore .env` reporta el archivo ignorado y `.env.example` lista cada variable del plan con comentario (AC-1, AC-2, AC-4)_
- [ ] T2 @backend-expert: Crear `backend/pyproject.toml`, `.python-version`, `app/__init__.py` y `uv.lock` con las libs por tag, Ruff, mypy y pytest — _outcome: `uv sync`, `uv run python -c "import market_data_client, matriz_client"`, `ruff check`, `ruff format --check` y `mypy .` salen con exit 0 (AC-5, AC-6, AC-12, AC-13, AC-15, NFR-1, NFR-5)_
- [ ] T3 @frontend-expert: Crear el toolchain del frontend (`package.json` con scripts `generate:api` y `e2e`, lockfile, `vite.config.ts` con lint/fmt/test, alias y `envDir`, `tsconfig*.json`, `index.html`, `src/main.tsx` mínimo y `src/vite-env.d.ts`) — _outcome: `vp install`, `vp build`, `vp lint` y `vp fmt --check` salen con exit 0 (AC-17, AC-18, AC-22, AC-26, NFR-4)_

### Wave 2 (depends on T2, T3)
- [ ] T4 @backend-expert: Implementar `app/core/config.py`, `app/__main__.py` y `tests/conftest.py` + `tests/test_config.py` — _outcome: `python -m app` sin `DATABASE_URL` sale con exit 1 nombrando la variable, y `uv run pytest tests/test_config.py` pasa (AC-8, AC-9)_
- [ ] T5 @database-expert: Implementar `app/db/base.py` y `app/db/session.py` + `tests/test_db.py` — _outcome: `uv run pytest tests/test_db.py` pasa y mypy strict sigue en verde sin plugin de SQLAlchemy (AC-11, AC-16)_
- [ ] T6 @frontend-expert: Crear el shell de la app (`app/providers.tsx`, `app/router.tsx`, `app/theme.ts`, `api/queryClient.ts`, `layouts/RootLayout.tsx`, `constants/routes.ts`, `screens/NotFoundScreen/*`, `test/setup.ts`, `test/render.tsx` y los `.gitkeep`) con `HomeScreen` provisorio sin datos — _outcome: `vp test run` pasa `NotFoundScreen.test.tsx` vía `renderWithProviders`, y `src/` contiene los 11 directorios (AC-19, AC-20, AC-21, AC-27)_

### Wave 3 (depends on T4, T5)
- [ ] T7 @backend-expert: Implementar `schemas/health.py`, `api/routes/health.py`, `api/router.py`, `main.py` (`create_app`, `lifespan`) y `scripts/export_openapi.py`, generar `backend/openapi.json` y agregar `tests/test_health.py`, `tests/test_openapi_export.py` y `tests/test_tooling.py` — _outcome: `uv run pytest`, `ruff` y `mypy` en verde; `GET /api/openapi.json` y `GET /api/health` responden 200 y `openapi.json` coincide con `app.openapi()` (AC-6, AC-10, AC-13, AC-14)_

### Wave 4 (depends on T6, T7)
- [ ] T8 @frontend-expert: Crear `orval.config.ts` y `src/api/mutator.ts`, ejecutar `vp run generate:api`, conectar `HomeScreen` a `useGetHealth()` con estados de carga y error, y agregar `HomeScreen.test.tsx` — _outcome: `vp run generate:api` genera `src/api/generated/health/health.ts`; sin `openapi.json` sale con exit ≠ 0 nombrando la ruta; `vp check` y `vp test run` pasan; no hay `fetch(` fuera de `src/api/` (AC-23, AC-24, AC-25, AC-27, NFR-6)_
- [ ] T9 @backend-expert: Crear `backend/Dockerfile` (targets `dev`, `builder` y `prod` con `--mount=type=ssh`) y `backend/.dockerignore` — _outcome: `docker build --ssh default --target prod backend` sale con exit 0, la imagen no tiene git, ssh ni claves, y sin agente SSH el build falla (AC-30, AC-34, NFR-3)_
- [ ] T10 @frontend-expert: Crear `frontend/Dockerfile` (targets `dev`, `build` y `prod` nginx), `frontend/nginx.conf` y `frontend/.dockerignore` — _outcome: la imagen `prod` sirve `index.html` en :8080 sin Node y arranca aunque no exista el host `backend` (AC-30, AC-31)_

### Wave 5 (depends on T1, T8, T9, T10)
- [ ] T11: Crear `docker-compose.dev.yml` y `docker-compose.prod.yml` — _outcome: cada modo levanta db, backend y frontend (dev con reload y HMR), `up backend`/`up frontend` levantan solo lo necesario, el volumen `pgdata` tiene nombre y sin `.env` falla con el mensaje de copiar `.env.example` (AC-29, AC-30, AC-31, AC-32, AC-33)_
- [ ] T12 @frontend-expert: Crear `playwright.config.ts` y `e2e/home.spec.ts` (mock de `/api/health` con `page.route`, home y 404) — _outcome: `vp run e2e` sale con exit 0 (AC-28)_
- [ ] T13 @docs-expert: Escribir `CLAUDE.md` (a partir de `future-plans/frontend-quality-prompt.md` + convenciones backend + flujo Orval) y `README.md` — _outcome: ambos archivos contienen todas las secciones listadas en "Docs changes" (AC-7, AC-10, AC-34, AC-35, AC-36, NFR-6)_

### Wave 6 (depends on T11, T12, T13)
- [ ] T14: Ejecutar en un clon limpio cada comando del README en orden y los chequeos de la tabla Verification, midiendo los tiempos de los comandos de calidad — _outcome: todos los comandos salen con exit 0, cada comando de calidad tarda menos de 60 s y los desvíos quedan corregidos o registrados en Critical Decisions (AC-1, AC-3, AC-37, NFR-7)_

## Open Questions

- [ ] Las dos librerías traen un `.env.example` propio (credenciales Auth0/Primary). Como no se usan en esta etapa, sus variables **no** se agregan al `.env.example` raíz. Revisitar cuando se implemente la primera integración.
- [ ] El e2e usa un mock de `/api/health` con `page.route` y no golpea el backend real. ¿Agregamos más adelante un proyecto de Playwright contra `docker-compose.dev.yml`?
- [ ] Elegí pnpm como gestor de paquetes del frontend (lockfile `frontend/pnpm-lock.yaml`). Si Vite+ recomienda otro por defecto, T3 lo ajusta y lo registra.
- [ ] Postgres 17 (`postgres:17-alpine`) y el driver `psycopg` v3 async son defaults míos. Confirmar si hay una versión de servidor objetivo en producción.
- [ ] El proyecto no tiene CI (fuera de alcance). Los guards de drift (`test_openapi_export.py`, `git diff` sobre `generated/`) solo corren localmente hasta que exista un pipeline.

## Critical Decisions
### Critical Decision — T1: `.gitignore` con entradas extra además de las del plan
- **What**: además de lo listado en Affected files, `.gitignore` ignora `.env.*` (re-incluye `!.env.example`), `*.py[cod]`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `.DS_Store` y `.claude/settings.local.json`.
- **Why**: `.env.*` evita versionar variantes como `.env.local` (NFR-3); los caches de mypy/ruff/pytest los generan T2/T4/T7; `.claude/settings.local.json` es configuración personal.
- **Affects**: `./.gitignore`; ninguna tarea posterior cambia.

### Critical Decision — T3: Versiones reales de Vite+ y dependencias del frontend
- **What**: `vite-plus` fijado en `1.7.0` con `vite` aliasado a `npm:@voidzero-dev/vite-plus-core@8.3.8000` (dependencia directa y override); `typescript ~7.0.2`, `antd ^6`, `orval ^8`, `jsdom ^29` y `react-router ^7`; `packageManager: pnpm@12.23.0`; tipos de cliente vía `vite-plus/client`. La config de `vite.config.ts` usa `lazyPlugins`, `loadEnv` y el bloque `lint` del template oficial (`typeAware` + `typeCheck`, regla `vite-plus/prefer-vite-plus-imports`) más los `ignorePatterns` del plan; `envDir` es la ruta absoluta de la raíz.
- **Why**: es lo que genera `vp create vite -- --template react-ts` en la versión vigente; antd 6 y orval 8 son las majors estables actuales (el plan asumía 5 y 7). `react-router 8` y `jsdom ≥30` exigen Node ≥22.22, por eso se quedaron en v7 y v29 para seguir funcionando en Node 22.20.
- **Affects**: `frontend/package.json` y `frontend/pnpm-lock.yaml`; T6 (API de antd 6), T8 (config/salida de Orval 8 y forma del mutator) y T10 (imagen `node:22-slim` con pnpm 12).

### Critical Decision — T3: `frontend/pnpm-workspace.yaml` adicional y tsconfig sin `references`
- **What**: se agregó `frontend/pnpm-workspace.yaml` con el override de `vite`, `allowBuilds: { esbuild: true }` y el `minimumReleaseAgeExclude` que escribe pnpm. `tsconfig.json` (app, `include: ["src"]`) y `tsconfig.node.json` (configs de la raíz) son independientes, sin `references`/`composite`.
- **Why**: pnpm 12 lee overrides y aprobación de builds solo desde ese archivo, y sin aprobar `esbuild` (lo usa orval) `vp install` falla con `ERR_PNPM_IGNORED_BUILDS`. El type-check de `vp lint` rechaza un proyecto referenciado con `noEmit`.
- **Affects**: el Affected files row de `frontend/tsconfig.json`; T10 debe copiar `pnpm-workspace.yaml` a la imagen junto con `package.json` y el lockfile.

### Critical Decision — T4: `conftest.py` sin fixture `client` todavía
- **What**: `tests/conftest.py` solo define el fixture autouse `test_env` (setea `DATABASE_URL` de test); el fixture `client: AsyncClient` no se creó. También se agregaron `app/core/__init__.py` y `tests/__init__.py` vacíos.
- **Why**: `create_app()` se implementa en T7 (`app/main.py`), así que un fixture que lo importe rompería la colección de tests en esta ola.
- **Affects**: T7 debe agregar el fixture `client` a `backend/tests/conftest.py`.

### Critical Decision — T5: `app/db/__init__.py` vacío
- **What**: se agregó `backend/app/db/__init__.py` vacío, que no figura en Affected files.
- **Why**: mantiene `app.db` como paquete regular, igual que `app/core/` (T4), para que pytest y mypy resuelvan `app.db.base`/`app.db.session` sin depender de namespace packages.
- **Affects**: la tabla Affected files (fila implícita para `backend/app/db/`); ninguna tarea posterior.

### Critical Decision — T6: `renderWithProviders` acepta `routes`, `HomeScreen` provisorio y `NODE_ENV`
- **What**: `renderWithProviders(ui, { route, routes })` monta un `createMemoryRouter` (no `MemoryRouter`): con `routes` usa ese árbol (así `NotFoundScreen.test.tsx` prueba el `*` real de `app/router.tsx`) y sin él monta `ui` en `*`. `HomeScreen` provisorio (`Result status="info"`) más `screens/HomeScreen/index.ts` se crearon ya, porque la ruta index lo importa de forma lazy. `src/main.tsx` monta `<AppProviders><AppRouter/></AppProviders>`. `test/setup.ts` importa `@testing-library/jest-dom/vitest` y usa `afterEach(cleanup)` de `vite-plus/test`. `router.tsx` exporta `routes` y `AppRouter` como dice el plan, lo que genera un warning (no error) de `react/only-export-components`.
- **Why**: el contrato del plan (`opts.route` + `MemoryRouter`) no permite renderizar el árbol de rutas real. Además, en una shell con `NODE_ENV=production` exportado, React carga su build de producción sin `act` y `vp test run` falla (`React.act is not a function`); con `NODE_ENV` sin definir (lo normal) pasa.
- **Affects**: `frontend/src/test/render.tsx`, `frontend/src/main.tsx`, `frontend/src/screens/HomeScreen/*`; T8 reemplaza el `HomeScreen` provisorio; T14/README deberían advertir que no se exporte `NODE_ENV=production` al correr los tests (o se puede forzar `test.env.NODE_ENV = "test"` en `vite.config.ts`).

### Critical Decision — T7: `__init__.py` de paquetes, helper `render_openapi()` y fixture `client`
- **What**: se agregaron `app/api/__init__.py`, `app/api/routes/__init__.py`, `app/schemas/__init__.py` y `app/scripts/__init__.py` vacíos; `export_openapi.py` expone `render_openapi() -> str` (lo usa `main()` y `test_openapi_export.py` para verificar también el formato byte a byte); el fixture `client` se agregó a `tests/conftest.py`, como dejó pendiente T4. `test_tooling.py` invoca Ruff como `sys.executable -m ruff ... --no-cache` para no depender del PATH.
- **Why**: paquetes regulares como en `app/core` y `app/db` (T4/T5); el test de drift detecta tanto cambios de contenido como un export hecho a mano con otro formato.
- **Affects**: `backend/app/scripts/export_openapi.py`, `backend/tests/conftest.py`; ninguna tarea posterior.

### Critical Decision — T8: `HomeScreen.test.tsx` mockea `fetch` y ajustes de Orval v8 / `erasableSyntaxOnly`
- **What**: `HomeScreen.test.tsx` usa `vi.stubGlobal("fetch", …)` en lugar de precargar un `QueryClient` con `setQueryData(getGetHealthQueryKey(), …)`, y cubre los estados de carga, éxito y error; `orval.config.ts` no lleva `prettier: false` (Orval 8.49 ya no acepta esa opción); `ApiError` declara `status`/`body` como campos explícitos en vez de parameter properties; `customFetch` devuelve `{ data, status, headers }` (el shape de `httpClient: 'fetch'`), con el `as T` genérico que exige el mutator.
- **Why**: `renderWithProviders()` (T6) crea su propio `QueryClient` y no acepta uno externo; mockear `fetch` además ejercita el mutator real sin tocar `src/test/render.tsx` ni sumar MSW. El tsconfig tiene `erasableSyntaxOnly`, que prohíbe parameter properties. `fetch` en tests no viola AC-25 (es `vi.stubGlobal`, no una llamada `fetch(`). AC-24 se cumple con Orval directo: sin el archivo sale con exit 1 y `ENOENT … open '…/backend/openapi.json'`, así que no hizo falta el wrapper con `node -e`.
- **Affects**: `frontend/orval.config.ts`, `frontend/src/api/mutator.ts`, `frontend/src/screens/HomeScreen/HomeScreen.test.tsx`; T13 (CLAUDE.md puede documentar el patrón de test con `vi.stubGlobal`), T14 (`vp test run` falla con `React.act is not a function` si el shell exporta `NODE_ENV=production`, porque Vitest respeta el valor existente y carga el build de producción de React; se corre con `NODE_ENV=test` o sin esa variable).

### Critical Decision — T10: stage `deps` compartido e instalación con `pnpm install`
- **What**: `frontend/Dockerfile` agrega un stage `deps` (`node:22-slim` + `corepack enable`, copia `package.json`, `pnpm-lock.yaml` y `pnpm-workspace.yaml`, y ejecuta `pnpm install --frozen-lockfile` con cache de store) del que heredan `dev` y `build`; `build` corre `vp build` en lugar de `vp install --frozen-lockfile && vp build`. `nginx.conf` suma `server_name _`, `index index.html` y un `location /assets/` con cache inmutable.
- **Why**: `vp` es un binario local de `vite-plus` (`node_modules/.bin/vp`), así que no existe antes de instalar las dependencias; pnpm 12.23.0 se obtiene por `packageManager` vía corepack. El stage común evita instalar dos veces. Verificado: la imagen `prod` (nginx-unprivileged, uid 101, sin `node`) sirve `index.html` y el fallback SPA en :8080 sin host `backend`, y `/api/health` responde 502 hasta que el backend exista.
- **Affects**: `frontend/Dockerfile`, `frontend/nginx.conf`; T11 (el servicio `frontend` dev ya tiene `node_modules` en la imagen, que inicializa el volumen anónimo `/app/node_modules`).

### Critical Decision — T13: `CLAUDE.md` adapta la guía de calidad a lo que existe hoy
- **What**: la "Definición de terminado" del frontend usa `vp test run` sin `--coverage` ni umbrales de cobertura, y el patrón de mock documentado es `vi.stubGlobal("fetch", …)` en lugar de los mocks MSW de Orval; el README instala `vp` con `npm install -g vite-plus` y pnpm con `corepack enable`.
- **Why**: `future-plans/frontend-quality-prompt.md` exige cobertura y MSW, pero el esqueleto no tiene proveedor de cobertura ni MSW instalados (T8), así que documentarlos daría comandos que fallan (AC-37). `vp` es un binario local de `vite-plus` y hace falta una instalación global para correr `vp install` antes de tener `node_modules`.
- **Affects**: `CLAUDE.md` §8–§9, `README.md` (Prerrequisitos y Frontend local); T14 valida esos comandos en el clon limpio.

### Critical Decision — T14: el README instala `vp` con el instalador oficial, no con `npm install -g`
- **What**: `README.md` (Prerrequisitos) pasa a indicar `curl -fsSL https://vite.plus | bash` y advierte no usar `npm install -g vite-plus`. Esto reemplaza lo que decía la Critical Decision de T13.
- **Why**: en el clon limpio, con `vp` instalado por `npm install -g vite-plus@1.7.0`, `vp test run` sale con exit 1 (`Cannot find package 'jsdom'`): el paquete npm global corre su propio Vitest, que no resuelve `jsdom` del proyecto. Con el instalador oficial (probado en un `HOME` temporal, `VP_VERSION=1.7.0`) todo el flujo del frontend sale con exit 0.
- **Affects**: `README.md`; ningún archivo de código.

### Critical Decision — T14: resultado de la verificación en el clon limpio y chequeos Docker pendientes
- **What**: el repo no tiene commits, así que el "clon limpio" se armó copiando `git ls-files -co --exclude-standard` a un repo temporal y clonándolo con `git clone`. Salieron con exit 0: `cp .env.example .env`, `git check-ignore .env` (AC-2), sin otros `.env` (AC-3), `uv sync` y los imports (AC-5/6), `uv sync` sin SSH con exit 1 (AC-7), `python -m app --reload` (`/api/openapi.json`, `/api/docs` y `/api/health` devuelven 200), `python -m app` con `DATABASE_URL=""` o `BACKEND_PORT=abc` (exit 1, nombra la variable), `export_openapi` sin diff, `corepack enable`, `vp install`, `vp build`, `vp run generate:api` sin diff y exit 1 con `ENOENT …/backend/openapi.json` si falta el archivo (AC-24), AC-25, AC-18, AC-4, `vp exec playwright install chromium` y `vp run e2e` (2 tests), `docker compose … config` en ambos modos y su error sin `.env` (AC-33), y `docker compose -f docker-compose.dev.yml up -d db` (volumen `matriz-trader-dev_pgdata`). Tiempos (NFR-7): `ruff check` 0,7 s, `ruff format --check` 0,2 s, `mypy` 5,9 s, `pytest` 7,8 s (18 tests), `vp lint` 3,0 s, `vp fmt --check` 0,6 s, `vp check` 0,5 s y `vp test run` 2,0 s (5 tests). `vp lint`/`vp check` muestran 1 warning conocido (`react/only-export-components` en `router.tsx`, CD T6).
- **Why**: los `up --build` de Compose (AC-29 a AC-32 y AC-34 con build) no se pudieron ejecutar en esta máquina: el daemon de Docker Desktop se queda colgado resolviendo `docker/dockerfile:1.7` (también con `docker pull`, más de 10 minutos), aunque el registry responde por `curl`. Es un problema del entorno, no de los archivos.
- **Affects**: AC-29, AC-30, AC-31, AC-32 y AC-34 siguen sin verificarse de punta a punta en T14 y hay que repetirlos cuando Docker pueda descargar imágenes. La shell del usuario exporta `NODE_ENV=production`, así que los comandos del frontend se corrieron sin esa variable, como advierten el README y la CD de T8.
