# syntax=docker/dockerfile:1.7
#
# Targets:
#   dev     -> dependencias completas (incluye dev) y `python -m app --reload`
#   builder -> venv de producción (sin dev) + código de la app
#   prod    -> python:3.13-slim limpia: solo el venv y app/, sin git, ssh ni known_hosts
#
# Las libs de gravity-quant/market-libs se instalan por SSH. La clave nunca entra en
# la imagen: se monta solo durante `uv sync` con `RUN --mount=type=ssh`.
#   docker build --ssh default --target prod backend
# Sin agente SSH (o sin clave cargada) el `uv sync` falla y el build sale con exit != 0.

FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH
RUN apt-get update \
 && apt-get install -y --no-install-recommends git openssh-client \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p -m 0700 /root/.ssh \
 && ssh-keyscan github.com >> /root/.ssh/known_hosts
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./

FROM base AS dev
RUN --mount=type=ssh uv sync --frozen
COPY app ./app
EXPOSE 8000
CMD ["python", "-m", "app", "--reload"]

FROM base AS builder
RUN --mount=type=ssh uv sync --frozen --no-dev
COPY app ./app

FROM python:3.13-slim AS prod
ENV PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/app ./app
USER app
EXPOSE 8000
CMD ["python", "-m", "app"]
