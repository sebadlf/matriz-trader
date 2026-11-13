# CLAUDE.md — Matriz Trader (monorepo)

## Estructura

- `frontend/` — Vite + React + TS + antd + Orval/react-query (npm, aislado). Ver `frontend/CLAUDE.md`.
- `backend/` — FastAPI (`GET /health`, `/accounts`, `/instruments`, `/orders`, `/orders/cancel`). Ver `backend/CLAUDE.md`.
- `worker/` — proceso long-running: login en Matriz (vía `broker`) y `market-data-client` (market data). Ver `worker/CLAUDE.md`.
- `broker/` — `matriz-broker`: único dueño de `matriz-client` (sesión y órdenes contra Matriz), usado por `backend` y `worker`. Ver `broker/CLAUDE.md`.
- `model/` — base SQLAlchemy 2, engine/sesión y Alembic compartidos. Ver `model/CLAUDE.md`.
- `e2e/` — Playwright (Python) contra el stack levantado. Ver `e2e/CLAUDE.md`.
- `scripts/check.sh` — gate de calidad completo; `scripts/check-versions.sh` — versiones de Python/Node.
- `docker-compose.yml` — modo producción (`postgres`, `backend`, `worker`, `frontend` con nginx).
- `.octo/specs/` — specs y planes; no es código.

`model`, `broker`, `backend`, `worker` y `e2e` forman un único workspace `uv` (`pyproject.toml` raíz, un solo `uv.lock`). Ruff y Pyright strict se configuran solo en el `pyproject.toml` raíz.

## Convenciones

- Un único `.env` en la raíz (plantilla: `.env.example`). Nunca crear `.env` por proyecto ni commitear secretos.
- Paquetes Python con layout `src/`; distribución `matriz-<x>`, import corto (`import model`, `import broker`, `import backend`, `import worker`). Cada paquete tiene `py.typed`.
- SQLAlchemy solo con `DeclarativeBase`, `Mapped[]` y `mapped_column()`, sin plugins.
- Pyright strict sin `# type: ignore` globales; los ignores van puntuales y con regla (`# pyright: ignore[reportCallIssue]` al instanciar settings de pydantic-settings).
- `frontend/openapi.json` es el contrato versionado; se regenera con `uv run python -m backend.export_openapi`, nunca a mano.
- El market data se obtiene siempre con `market-data-client`; nunca con `matriz-client`. Único punto de acceso: `worker/src/worker/market_data_gateway.py` (ningún otro módulo importa `market_data_client`).
- Matriz (login, órdenes, instrumentos) se accede siempre con `matriz-client`, declarado solo en `broker/pyproject.toml`. Único punto de acceso: `broker/src/broker/matriz_gateway.py` (ningún otro módulo importa `matriz_client`).
- Las cuentas operables salen de `MATRIZ_ACCOUNTS` en el `.env` raíz (lista separada por comas, la lee el backend); no hay tabla de cuentas.

## Credenciales de Postgres y el volumen `pgdata`

`POSTGRES_USER`/`POSTGRES_PASSWORD` solo se aplican cuando el volumen `pgdata` está vacío. Cambiarlos
en el `.env` después no modifica el rol existente: `pg_isready` sigue `healthy`, pero el backend recibe
`password authentication failed for user "matriz"`, `/health` responde 503 y `docker compose up` aborta
con `container matriz-trader-backend-1 is unhealthy`. El backend lo loguea (`Database unavailable: …`).

Realinear conservando los datos (toma la contraseña nueva del entorno del contenedor):

```bash
docker compose up -d postgres            # recrea el contenedor con el .env actual
docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v pw="$POSTGRES_PASSWORD" <<SQL
ALTER ROLE CURRENT_USER WITH PASSWORD :'"'"'pw'"'"';
SQL'
docker compose up --build
```

Alternativa destructiva (⚠️ **borra todos los datos** de la base): `docker compose down -v && docker compose up --build`.

## Comandos (desde la raíz)

```bash
cp .env.example .env
uv sync
cd frontend && npm ci --include=dev            # --include=dev: el shell puede tener NODE_ENV=production

scripts/check.sh                               # todos los gates (correr antes de dar algo por terminado)
uv run ruff check . && uv run ruff format --check .
uv run pyright                                 # sin argumentos: `uv run pyright worker` sale 0 aunque haya errores

docker compose up postgres                     # solo la BD para dev
uv run uvicorn backend.main:app --reload --port 8000
uv run python -m worker
cd frontend && npm run dev

docker compose up --build                      # producción → http://localhost:8080
uv run pytest e2e                              # con el stack levantado
```

Node 24 (`.nvmrc`, `nvm use`) y Python 3.13 (`.python-version`).
