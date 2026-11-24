# matriz-trader

Cliente de trading construido sobre las librerías internas `market-data-client` (v0.7.1) y `matriz-client` (v0.4.0) del repositorio `gravity-quant/market-libs`.

Por ahora el repo es solo el esqueleto del monorepo, sin funcionalidad de negocio:

- `backend/`: Python 3.13 + FastAPI + SQLAlchemy 2.0 (async) + Pydantic, gestionado con uv. Expone un único endpoint, `GET /api/health`.
- `frontend/`: React + TypeScript sobre Vite+ (`vp`), con Ant Design, React Router, Zustand y un cliente generado con Orval (react-query).
- PostgreSQL 17, dos archivos de Docker Compose (`docker-compose.dev.yml` y `docker-compose.prod.yml`) y un único `.env` en la raíz.

Las convenciones de código están en [`CLAUDE.md`](CLAUDE.md) (contexto, gates, Definición de terminado y checklist), [`backend/CLAUDE.md`](backend/CLAUDE.md) y [`frontend/CLAUDE.md`](frontend/CLAUDE.md) (estructura, reglas de dependencia y flujo de regeneración del cliente Orval).

## Prerrequisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.13 | Backend (uv lo puede instalar por vos) |
| [uv](https://docs.astral.sh/uv/) | ≥ 0.9 | Dependencias y comandos del backend |
| Node.js | 22 | Frontend |
| pnpm | la fijada en `frontend/package.json` (`packageManager`) | Se activa con `corepack enable` |
| Vite+ (`vp`) | 1.7 | CLI del frontend: instalador oficial (ver abajo) |
| Docker + Docker Compose | Compose ≥ 2.24 | Modo contenedores (dev y prod) y gate `migrations` (testcontainers) |
| Acceso SSH a `github.com/gravity-quant/market-libs` | — | Instalar `market-data-client` y `matriz-client` |
| [lefthook](https://lefthook.dev/) | ≥ 2.2 | Hooks de git (`pre-commit` y `commit-msg`) |
| [gitleaks](https://github.com/gitleaks/gitleaks) | ≥ 8.30 | Detección de secretos en cada commit |
| [jq](https://jqlang.org/) | cualquiera | Hooks de Claude Code (`.claude/hooks/`); en macOS viene en `/usr/bin/jq` |
| [OSV-Scanner](https://google.github.io/osv-scanner/) | 2.7 | Solo para correr `scripts/audit.py` en local |

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

El backend también exige las credenciales de las librerías internas: `PRIMARY_USER` y `PRIMARY_PASSWORD` (`matriz-client`), y `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE` y `MARKET_DATA_AUTH0_TOKEN_URL` (`market-data-client`). Si falta alguna o está vacía, el backend no arranca y nombra la variable en stderr. `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` son opcionales y, por defecto, apuntan a entornos de prueba (reMarkets y market data develop).

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

Todos los gates son bloqueantes y se definen en un único script, `scripts/gate.sh`. Lo invocan los hooks de git (lefthook), los hooks de Claude Code (`.claude/settings.json`), el hook de Octo y GitHub Actions, así que lo que pasa en tu máquina es lo mismo que corre en CI. La tabla de qué corre en cada momento está en [`CLAUDE.md`](CLAUDE.md#4-gates-y-dónde-corren).

### Correr los gates

Desde la raíz del repo, con las dependencias de ambos módulos instaladas (`uv sync` en `backend/` y `vp install` en `frontend/`):

```bash
scripts/gate.sh backend          # Ruff, mypy, import-linter, pytest (cobertura ≥ 85 %) y probes de guardas
scripts/gate.sh frontend         # vp check, dependency-cruiser, knip, Vitest (cobertura ≥ 70 %), build, size-limit y probes
scripts/gate.sh e2e              # Playwright + accesibilidad con axe
scripts/gate.sh migrations       # Alembic contra PostgreSQL 17 (testcontainers, requiere Docker) + Squawk
scripts/gate.sh changed          # el gate completo de cada módulo con cambios sin commitear
scripts/gate.sh backend quick    # versión rápida, la que corre en el pre-commit
```

Antes de `scripts/gate.sh e2e`, descargá una vez el navegador de Playwright: `cd frontend && vp exec playwright install chromium`.

El script usa el `vp` de `frontend/node_modules/.bin` y hace `unset NODE_ENV`. Si corrés `vp test` a mano, no exportes `NODE_ENV=production` en la shell: Vitest carga el build de producción de React y los tests fallan con `React.act is not a function`.

Los comandos sueltos de cada módulo están en [`backend/CLAUDE.md`](backend/CLAUDE.md#1-comandos-desde-backend) y [`frontend/CLAUDE.md`](frontend/CLAUDE.md#1-comandos-desde-frontend).

### Hooks de git (lefthook y gitleaks)

```bash
brew install lefthook gitleaks   # o: uv tool install lefthook
lefthook install                 # en la raíz: instala pre-commit y commit-msg desde lefthook.yml
```

- `pre-commit` corre `scripts/gate.sh <módulo> quick` para cada módulo con archivos stageados (y re-stagea lo que formatea), bloquea los commits que cambian `frontend/src/api/generated/` sin `backend/openapi.json` y busca secretos con gitleaks. Si `gitleaks` no está instalado, el commit falla.
- `commit-msg` exige Conventional Commits: `<tipo>(<scope>)?: <descripción>`, con tipo en `feat|fix|chore|docs|refactor|test|perf|ci|build` y primera línea de hasta 72 caracteres. Ejemplo: `feat(backend): agrega Clock inyectable`.

No uses `--no-verify`: CI corre los mismos gates en modo completo.

### Hooks de Claude Code y Octo

`.claude/settings.json` está versionado y se activa solo al abrir el repo con Claude Code (necesita `jq`):

- `PreToolUse` bloquea la edición de archivos generados o protegidos (`frontend/src/api/generated/`, `backend/openapi.json`, `.env*`, los lockfiles) e indica el comando que los regenera.
- `PostToolUse` formatea y lintea cada archivo `.py`, `.ts` o `.tsx` que edita el agente.
- `Stop` corre `scripts/gate.sh changed full` antes de que el agente termine el turno; si falla, el agente recibe la salida y sigue trabajando.

El hook de Octo (`.octo/hooks/code-validate-improve.json`) corre `scripts/gate.sh branch full` al cerrar cada wave.

### Regenerar el cliente de la API

Después de cambiar endpoints del backend:

```bash
cd backend && uv run python -m app.scripts.export_openapi    # actualiza backend/openapi.json
cd ../frontend && vp run generate:api                        # regenera src/api/generated/
```

Commiteá juntos `backend/openapi.json` y `frontend/src/api/generated/`. El detalle está en [`frontend/CLAUDE.md`](frontend/CLAUDE.md#flujo-para-cambiar-el-contrato).

### CI (GitHub Actions)

`.github/workflows/ci.yml` corre en cada PR contra `main` y en cada push a `main`. Los jobs `backend`, `frontend`, `e2e` y `migrations` se omiten si el PR no toca su módulo; `security` (gitleaks sobre los commits del PR y `scripts/audit.py`) y `workflow-lint` (actionlint y zizmor) corren siempre. El job `ci-ok` agrega los resultados y es el único check que exige el ruleset.

#### Secret `MARKET_LIBS_TOKEN`

Los jobs `backend` y `migrations` instalan `market-libs` por HTTPS con el secret `MARKET_LIBS_TOKEN`. Sin él, fallan con `Falta el secret MARKET_LIBS_TOKEN`. Para crearlo:

1. En GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**, generá un token con *Resource owner* `gravity-quant`, acceso solo al repositorio `market-libs`, permiso **Contents: Read-only** y vencimiento de 90 días. Si la organización exige aprobación de tokens, un admin de `gravity-quant` tiene que aprobarlo.
2. Guardalo como secret de Actions del repo:

   ```bash
   gh secret set MARKET_LIBS_TOKEN    # pegá el token cuando lo pida
   ```

3. Agendá la rotación antes del vencimiento: cuando el token vence, los jobs `backend` y `migrations` fallan en `uv sync`.

Como mejora, el token se puede reemplazar por una GitHub App de la organización con permiso `Contents: Read` sobre `market-libs` (`actions/create-github-app-token` con los secrets `MARKET_LIBS_APP_ID` y `MARKET_LIBS_APP_KEY`), que no depende de una cuenta personal. Requiere un admin de `gravity-quant` y cambiar el paso «Acceso a market-libs» de `ci.yml`.

#### Ruleset de `main`

`.github/rulesets/main.json` define la protección de `main`:

- todo cambio entra por PR, con los hilos de revisión resueltos (hoy sin aprobaciones obligatorias, porque hay un solo mantenedor);
- el check `ci-ok` es obligatorio y la rama tiene que estar actualizada con `main`;
- sin force-push ni borrado de la rama.

Se aplica una vez, con permisos de admin sobre el repo:

```bash
gh api repos/{owner}/{repo}/rulesets -X POST --input .github/rulesets/main.json
```

`gh` reemplaza `{owner}` y `{repo}` con los del repo actual. Queda visible en Settings → Rules → Rulesets. Para cambiarlo después, editá el JSON y usá `gh api repos/{owner}/{repo}/rulesets/<id> -X PUT --input .github/rulesets/main.json` (el `<id>` sale de `gh api repos/{owner}/{repo}/rulesets`).

#### Auditoría de dependencias

`scripts/audit.py` corre pip-audit sobre el `uv.lock` exportado (sin las fuentes git de `market-libs`) y OSV-Scanner sobre `frontend/pnpm-lock.yaml`. Falla ante cualquier vulnerabilidad que no esté en `security-allowlist.toml`. Cada entrada de la allowlist lleva `id`, `ecosystem`, `package`, `reason` y `expires` (por convención, como máximo 90 días desde que se agrega); una entrada vencida o incompleta también hace fallar el job.

```bash
brew install osv-scanner
python3 scripts/audit.py         # si python3 es < 3.11, se re-ejecuta solo con uv
```

### Renovate

`renovate.json` configura las actualizaciones automáticas de dependencias. Para activarlo, un admin instala la [app de Renovate](https://github.com/apps/renovate) con acceso a `matriz-trader` y a `gravity-quant/market-libs`; sin acceso a `market-libs`, Renovate no puede seguir los tags de las librerías internas.

- Espera 7 días desde la publicación de una versión antes de proponerla (`minimumReleaseAge`).
- Agrupa los PRs en `backend`, `frontend`, `github-actions` (actualiza los SHA de las acciones fijadas), `vite-plus` (`vite-plus` junto con `@vitest/coverage-v8`, que tiene que usar el mismo Vitest) y `market-libs` (tags `market-data-client-vX.Y.Z` y `matriz-client-vX.Y.Z`, sin espera).
- Las versiones y los SHA-256 de los binarios que descarga `ci.yml` (actionlint, gitleaks, OSV-Scanner, en el bloque `env`) no los actualiza Renovate: se suben a mano.

Para validar un cambio en `renovate.json`:

```bash
npx --yes --package renovate -- renovate-config-validator renovate.json
```

La versión actual del validador requiere Node ≥ 24; con Node 22, `npx` resuelve una versión anterior que también sirve.

## Troubleshooting de SSH

| Síntoma | Causa probable | Solución |
|---|---|---|
| `uv sync` falla con `Permission denied (publickey)` | Tu clave no está registrada en GitHub o no tiene acceso a `market-libs` | Revisá `ssh -T git@github.com` y pedí acceso al repositorio |
| `uv sync` falla con `Host key verification failed` | `github.com` no está en `~/.ssh/known_hosts` | Ejecutá `ssh -T git@github.com` una vez y aceptá la huella |
| El build Docker del backend falla en `uv sync` | El `ssh-agent` no está corriendo o no tiene la clave | `eval "$(ssh-agent -s)" && ssh-add`, verificá con `ssh-add -l` y reconstruí |
| `docker build` falla aunque `ssh-add -l` lista la clave | Falta reenviar el agente | Agregá `--ssh default` (Compose ya lo hace con `ssh: [default]`) |
| La clave tiene passphrase y el build se queda esperando | El agente no tiene la clave desbloqueada | Cargala con `ssh-add` antes de construir (en macOS: `ssh-add --apple-use-keychain`) |
