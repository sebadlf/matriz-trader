# matriz-trader

Cliente de trading construido sobre las librerías internas `market-data-client` (v0.7.1) y `matriz-client` (v0.4.0) del repositorio `gravity-quant/market-libs`.

Por ahora el repo es solo el esqueleto del monorepo, sin funcionalidad de negocio:

- `backend/`: Python 3.13 + FastAPI + SQLAlchemy 2.0 (async) + Pydantic, gestionado con uv. Expone un único endpoint, `GET /api/health`.
- `frontend/`: React + TypeScript sobre Vite+ (`vp`), con Ant Design, React Router, Zustand y un cliente generado con Orval (react-query).
- PostgreSQL 17, dos archivos de Docker Compose (`docker-compose.dev.yml` y `docker-compose.prod.yml`) y un único `.env` en la raíz.

Las convenciones de código, la estructura de carpetas y el flujo de regeneración del cliente Orval están en [`CLAUDE.md`](CLAUDE.md).

## Prerrequisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.13 | Backend (uv lo puede instalar por vos) |
| [uv](https://docs.astral.sh/uv/) | ≥ 0.9 | Dependencias y comandos del backend |
| Node.js | 22 | Frontend |
| pnpm | la fijada en `frontend/package.json` (`packageManager`) | Se activa con `corepack enable` |
| Vite+ (`vp`) | 1.7 | CLI del frontend: instalador oficial (ver abajo) |
| Docker + Docker Compose | Compose ≥ 2.24 | Modo contenedores (dev y prod) |
| Acceso SSH a `github.com/gravity-quant/market-libs` | — | Instalar `market-data-client` y `matriz-client` |

### Instalar Vite+ (`vp`)

Usá el instalador oficial, que deja `vp` en `~/.vite-plus/bin` y delega en el `vite-plus` local del proyecto:

```bash
curl -fsSL https://vite.plus | bash    # luego abrí una shell nueva (o cargá ~/.vite-plus/env)
vp --version
```

No lo instales con `npm install -g vite-plus`: esa variante ejecuta los tests con su propio Vitest global, que no encuentra `jsdom` del proyecto, y `vp test run` falla con `Cannot find package 'jsdom'`.

### Acceso SSH a `market-libs`

Las dos librerías internas se instalan desde un repositorio privado por SSH (`backend/pyproject.toml`, sección `[tool.uv.sources]`). Necesitás una clave SSH registrada en GitHub con permiso de lectura sobre `gravity-quant/market-libs`. Comprobalo con:

```bash
ssh -T git@github.com
# Hi <usuario>! You've successfully authenticated, ...
```

**Sin ese acceso, `uv sync` falla con código de salida distinto de 0** (`Permission denied (publickey)`) y el backend no se puede instalar, ni localmente ni en Docker.

## Configuración

Todo el proyecto usa **un único `.env` en la raíz** (está en `.gitignore`). Lo leen el backend, el frontend y Docker Compose; no crees `.env` dentro de `backend/` ni de `frontend/`.

```bash
cp .env.example .env
```

Cada variable de `.env.example` tiene un comentario que explica su uso. Los valores de ejemplo sirven para desarrollo local; cambiá al menos `POSTGRES_PASSWORD` (y el `DATABASE_URL` que la contiene) fuera de tu máquina.

## Backend local

Requiere un PostgreSQL accesible en el `DATABASE_URL` del `.env`. La forma más simple es levantar solo la base con Compose:

```bash
docker compose -f docker-compose.dev.yml up -d db
```

Después, desde `backend/`:

```bash
cd backend
uv sync                          # crea .venv con Python 3.13 e instala todo (requiere acceso SSH)
uv run python -m app --reload    # servidor en http://localhost:8000 con recarga automática
```

- OpenAPI: <http://localhost:8000/api/openapi.json>
- Swagger UI: <http://localhost:8000/api/docs>
- Health: <http://localhost:8000/api/health>

Si falta una variable obligatoria o tiene un formato inválido, `python -m app` termina con código 1 y un mensaje `Configuración inválida: <VARIABLE>`.

## Frontend local

Desde `frontend/`:

```bash
cd frontend
corepack enable                  # activa la versión de pnpm fijada en package.json
vp install                       # instala las dependencias
vp dev                           # servidor de desarrollo en http://localhost:5173
```

El dev server hace proxy de `/api` al backend en `BACKEND_URL` (por defecto `http://localhost:8000`). La pantalla de inicio consulta `GET /api/health`; si el backend no está levantado, muestra un error.

## Docker Compose

Hay dos archivos independientes, uno por modo. Cada uno usa su propio nombre de proyecto (`matriz-trader-dev` / `matriz-trader-prod`), así que no comparten contenedores ni datos. PostgreSQL persiste en un volumen con nombre (`matriz-trader-dev_pgdata` / `matriz-trader-prod_pgdata`).

Si el `.env` de la raíz no existe, Compose falla con el mensaje `Falta .env en la raíz. Ejecutá cp .env.example .env`.

### Clave SSH para construir el backend

La imagen del backend instala `market-libs` por SSH durante el build. La clave **no se copia a la imagen**: se reenvía el `ssh-agent` de tu máquina solo durante el `uv sync` (`RUN --mount=type=ssh` en `backend/Dockerfile`, `ssh: [default]` en los archivos compose). Antes de construir, cargá la clave en el agente:

```bash
eval "$(ssh-agent -s)"           # si no tenés un agente corriendo
ssh-add                          # o: ssh-add ~/.ssh/<tu_clave>
ssh-add -l                       # debe listar la clave
```

Si el agente no tiene la clave, el build del backend falla con código de salida distinto de 0. Para construir la imagen sin Compose, pasá el agente explícitamente con `--ssh default`:

```bash
docker build --ssh default --target prod -t matriz-trader-backend backend
```

### Modo desarrollo

PostgreSQL, backend con recarga automática (`backend/app` montado) y frontend con `vp dev` y HMR (`frontend/` montado):

```bash
docker compose -f docker-compose.dev.yml up -d --build            # todo
docker compose -f docker-compose.dev.yml up -d --build backend    # solo db + backend
docker compose -f docker-compose.dev.yml up -d --build frontend   # solo frontend
docker compose -f docker-compose.dev.yml down                     # detener (los datos quedan en el volumen)
```

- Frontend: <http://localhost:5173> (`FRONTEND_PORT`)
- Backend: <http://localhost:8000/api/docs> (`BACKEND_PORT`)
- PostgreSQL: `localhost:5432` (`POSTGRES_PORT`)

### Modo producción

Imágenes sin dependencias ni servidores de desarrollo: el backend corre en una imagen `python:3.13-slim` limpia (sin git ni ssh) y el frontend es un nginx que sirve el build estático y hace proxy de `/api` al backend:

```bash
docker compose -f docker-compose.prod.yml up -d --build            # todo
docker compose -f docker-compose.prod.yml up -d --build backend    # solo db + backend
docker compose -f docker-compose.prod.yml up -d --build frontend   # solo frontend (nginx)
docker compose -f docker-compose.prod.yml down
```

- Aplicación: <http://localhost:8080> (`FRONTEND_PROD_PORT`); `/api/*` va al backend.
- Backend directo: <http://localhost:8000/api/openapi.json>

Si levantás solo el frontend, nginx arranca igual y `/api` responde 502 hasta que el backend exista.

## Calidad y tests

### Backend (desde `backend/`)

```bash
uv run ruff check .              # lint (incluye las reglas de anotaciones ANN)
uv run ruff format --check .     # formato (sin --check, formatea)
uv run mypy .                    # tipado strict con el plugin pydantic.mypy
uv run pytest                    # tests (no necesitan PostgreSQL)
```

### Frontend (desde `frontend/`)

```bash
vp lint                          # Oxlint + type-check
vp fmt --check                   # Oxfmt (sin --check, formatea)
vp check                         # formato + lint + type-check en un solo paso
vp test run                      # tests unitarios (Vitest + React Testing Library)
vp exec playwright install chromium   # una sola vez: descarga el navegador de Playwright
vp run e2e                       # tests e2e (levanta vp dev y mockea /api/health)
```

No exportes `NODE_ENV=production` en la shell al correr los tests: Vitest carga el build de producción de React y fallan con `React.act is not a function`.

### Regenerar el cliente de la API

Después de cambiar endpoints del backend:

```bash
cd backend && uv run python -m app.scripts.export_openapi    # actualiza backend/openapi.json
cd ../frontend && vp run generate:api                        # regenera src/api/generated/
```

Commiteá juntos `backend/openapi.json` y `frontend/src/api/generated/`. El detalle está en [`CLAUDE.md`](CLAUDE.md#5-acceso-al-backend-solo-vía-orval).

## Troubleshooting de SSH

| Síntoma | Causa probable | Solución |
|---|---|---|
| `uv sync` falla con `Permission denied (publickey)` | Tu clave no está registrada en GitHub o no tiene acceso a `market-libs` | Revisá `ssh -T git@github.com` y pedí acceso al repositorio |
| `uv sync` falla con `Host key verification failed` | `github.com` no está en `~/.ssh/known_hosts` | Ejecutá `ssh -T git@github.com` una vez y aceptá la huella |
| El build Docker del backend falla en `uv sync` | El `ssh-agent` no está corriendo o no tiene la clave | `eval "$(ssh-agent -s)" && ssh-add`, verificá con `ssh-add -l` y reconstruí |
| `docker build` falla aunque `ssh-add -l` lista la clave | Falta reenviar el agente | Agregá `--ssh default` (Compose ya lo hace con `ssh: [default]`) |
| La clave tiene passphrase y el build se queda esperando | El agente no tiene la clave desbloqueada | Cargala con `ssh-add` antes de construir (en macOS: `ssh-add --apple-use-keychain`) |
