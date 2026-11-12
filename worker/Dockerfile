# Imagen de producción del worker (AC-30, AC-40). Contexto de build: raíz del repo.
FROM python:3.13-slim

# git: uv lo necesita para resolver la fuente Git de market-data-client (uv.lock).
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.0 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias primero (capa cacheable): el lockfile necesita el pyproject de todos los miembros.
COPY pyproject.toml uv.lock ./
COPY model/pyproject.toml model/
COPY backend/pyproject.toml backend/
COPY worker/pyproject.toml worker/
COPY e2e/pyproject.toml e2e/
RUN uv sync --frozen --no-dev --package matriz-worker --no-install-workspace

COPY model/ model/
COPY worker/ worker/
RUN uv sync --frozen --no-dev --package matriz-worker

# Forma exec: PID 1 es Python y recibe SIGTERM directamente (AC-15).
CMD ["/app/.venv/bin/python", "-m", "worker"]
