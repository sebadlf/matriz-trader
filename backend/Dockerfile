# Imagen de producción del backend (AC-30, AC-40). Contexto de build: raíz del repo.
FROM python:3.13-slim

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
RUN uv sync --frozen --no-dev --package matriz-backend --no-install-workspace

COPY model/ model/
COPY backend/ backend/
RUN uv sync --frozen --no-dev --package matriz-backend

EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
