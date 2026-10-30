# CLAUDE.md — Matriz Trader (monorepo)

## Estructura

- `frontend/` — Vite + React + TS + antd + Orval/react-query (npm, aislado). Ver `frontend/CLAUDE.md`.
- `backend/` — FastAPI (`GET /health`). Ver `backend/CLAUDE.md`.
- `worker/` — proceso long-running con `matriz-client`. Ver `worker/CLAUDE.md`.
- `model/` — base SQLAlchemy 2, engine/sesión y Alembic compartidos. Ver `model/CLAUDE.md`.
- `e2e/` — Playwright (Python) contra el stack levantado. Ver `e2e/CLAUDE.md`.
- `scripts/check.sh` — gate de calidad completo; `scripts/check-versions.sh` — versiones de Python/Node.
- `docker-compose.yml` — modo producción (`postgres`, `backend`, `worker`, `frontend` con nginx).
- `.octo/specs/` — specs y planes; no es código.

`model`, `backend`, `worker` y `e2e` forman un único workspace `uv` (`pyproject.toml` raíz, un solo `uv.lock`). Ruff y Pyright strict se configuran solo en el `pyproject.toml` raíz.

## Convenciones

- Un único `.env` en la raíz (plantilla: `.env.example`). Nunca crear `.env` por proyecto ni commitear secretos.
- Paquetes Python con layout `src/`; distribución `matriz-<x>`, import corto (`import model`, `import backend`, `import worker`). Cada paquete tiene `py.typed`.
- SQLAlchemy solo con `DeclarativeBase`, `Mapped[]` y `mapped_column()`, sin plugins.
- Pyright strict sin `# type: ignore` globales; los ignores van puntuales y con regla (`# pyright: ignore[reportCallIssue]` al instanciar settings de pydantic-settings).
- `frontend/openapi.json` es el contrato versionado; se regenera con `uv run python -m backend.export_openapi`, nunca a mano.

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
