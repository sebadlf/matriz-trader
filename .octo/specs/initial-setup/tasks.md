# Tasks — Initial setup

### Wave 1

- [x] T1: Crear la configuración raíz (`git init`, `.gitignore`, `.env.example`, `.python-version`, `.nvmrc`, `.dockerignore`) — _outcome: `git check-ignore .env` coincide y `.env.example` contiene todas las variables del plan solo con valores de ejemplo (AC-25, AC-27, AC-44)_
- [x] T2: Scaffold de `frontend/` con Vite + React + TS strict, antd, react-router, react-query, Biome, ESLint flat config y Vitest, con una página placeholder — _outcome: `npm ci && npm run lint && npm run format:check` termina con exit 0 y genera `package-lock.json` (AC-4, AC-9, AC-39)_
- [x] T3: Crear `matriz-trader.code-workspace` y `.vscode/extensions.json` — _outcome: al abrir el workspace aparecen frontend/backend/worker/model y Biome/Ruff quedan como formateadores por defecto (AC-1, AC-2)_
- [x] T4: Descargar el wheel de `matriz-client` 0.3.0 a un directorio temporal aislado, verificar si la URL responde sin credenciales e inspeccionar el constructor, los métodos de conexión y cierre, los parámetros requeridos y `py.typed` — _outcome: `.octo/specs/initial-setup/matriz-client-notes.md` documenta público/privado, la firma real y los nombres finales de las variables `MATRIZ_*` (AC-16, AC-17)_

### Wave 2 (depends on T1, T4)

- [x] T5: Crear el `pyproject.toml` raíz (workspace, Ruff, Pyright strict), los `pyproject.toml` de `model`, `backend`, `worker` y `e2e` con paquetes vacíos, y la fuente URL de `matriz-client` — _outcome: `uv sync` genera un único `uv.lock` y `uv run python -c "import matriz_client"` funciona (AC-16, AC-22, AC-39)_

### Wave 3 (depends on T5)

- [x] T6: Implementar `model` (`config.py`, `base.py`, `db.py`, Alembic con `0001_initial` vacía) y sus unit tests — _outcome: `cd model && uv run pytest` pasa sin Postgres y `import model` expone `Base` y los factories (AC-19, AC-20, AC-21, AC-34, AC-36)_

### Wave 4 (depends on T6)

- [x] T7: Implementar el backend (`settings.py`, `health.py`, `main.py`, `export_openapi.py`) con tests de health, CORS, OpenAPI y env faltante — _outcome: `cd backend && uv run pytest` pasa cubriendo 200/503, CORS y `SystemExit(2)` (AC-10, AC-11, AC-12, AC-13, AC-34, AC-46)_
- [x] T8: Implementar el worker (`settings.py`, `matriz_gateway.py` según T4, `runner.py`, `__main__.py`, stub `.pyi` si hace falta) con tests de loop, señales y env faltante — _outcome: `cd worker && uv run pytest` pasa con `FakeGateway`, y `uv run pyright worker` reporta 0 errores (AC-14, AC-15, AC-17, AC-18, AC-24, AC-34, AC-36)_

### Wave 5 (depends on T2, T7, T8)

- [x] T9: Exportar `frontend/openapi.json`, configurar Orval + `http.ts` + `queryClient.ts` + router, implementar `HealthPage` con sus 3 tests y agregar `backend/tests/test_openapi_snapshot.py` — _outcome: con el backend apagado, `npm run build` y `npm test` terminan con exit 0, y la página muestra `health-loading`/`health-status`/`health-error` según el estado (AC-5, AC-6, AC-7, AC-8, AC-35, AC-45)_
- [x] T10: Crear `backend/Dockerfile`, `worker/Dockerfile` y `docker-compose.yml` con `postgres`, `backend` y `worker` (healthchecks, `depends_on`, volumen `pgdata`) — _outcome: `docker compose up --build postgres backend worker` deja backend `healthy` y `curl` dentro de la red devuelve `{"status":"ok","database":"ok"}` (AC-29, AC-32, AC-33, AC-40)_

### Wave 6 (depends on T9, T10)

- [x] T11: Crear `frontend/Dockerfile` y `frontend/nginx.conf`, y agregar el servicio `frontend` a `docker-compose.yml` — _outcome: `docker compose up --build` levanta los 4 servicios y `http://localhost:8080/` muestra `status: ok` y `database: ok` en menos de 120 s (AC-30, AC-31, AC-43)_

### Wave 7 (depends on T11)

- [x] T12: Implementar `e2e/tests/conftest.py` y `test_health_page.py` con Playwright — _outcome: con el stack levantado, `uv run pytest e2e` pasa, y con `E2E_BASE_URL` inválida termina con exit ≠ 0 (AC-37, AC-38)_
- [x] T13: Crear `scripts/check.sh` (todos los gates) y `scripts/check-versions.sh` — _outcome: ambos scripts terminan con exit 0 sobre el repo (AC-23, AC-24, AC-40, AC-41)_
- [x] T14: Escribir `README.md` y los `CLAUDE.md` de la raíz, `frontend`, `backend`, `worker`, `model` y `e2e` con los comandos verificados — _outcome: cada comando documentado se ejecuta tal cual sobre un clon limpio (AC-3, AC-28, AC-42)_
