# Tasks — Quiero crear las bases para un proyecto de

### Wave 1
- [x] T1: Crear `.gitignore` y `.env.example` en la raíz con todas las variables comentadas — _outcome: `git check-ignore .env` reporta el archivo ignorado y `.env.example` lista cada variable del plan con comentario (AC-1, AC-2, AC-4)_
- [x] T2 @backend-expert: Crear `backend/pyproject.toml`, `.python-version`, `app/__init__.py` y `uv.lock` con las libs por tag, Ruff, mypy y pytest — _outcome: `uv sync`, `uv run python -c "import market_data_client, matriz_client"`, `ruff check`, `ruff format --check` y `mypy .` salen con exit 0 (AC-5, AC-6, AC-12, AC-13, AC-15, NFR-1, NFR-5)_
- [x] T3 @frontend-expert: Crear el toolchain del frontend (`package.json` con scripts `generate:api` y `e2e`, lockfile, `vite.config.ts` con lint/fmt/test, alias y `envDir`, `tsconfig*.json`, `index.html`, `src/main.tsx` mínimo y `src/vite-env.d.ts`) — _outcome: `vp install`, `vp build`, `vp lint` y `vp fmt --check` salen con exit 0 (AC-17, AC-18, AC-22, AC-26, NFR-4)_

### Wave 2 (depends on T2, T3)
- [x] T4 @backend-expert: Implementar `app/core/config.py`, `app/__main__.py` y `tests/conftest.py` + `tests/test_config.py` — _outcome: `python -m app` sin `DATABASE_URL` sale con exit 1 nombrando la variable, y `uv run pytest tests/test_config.py` pasa (AC-8, AC-9)_
- [x] T5 @database-expert: Implementar `app/db/base.py` y `app/db/session.py` + `tests/test_db.py` — _outcome: `uv run pytest tests/test_db.py` pasa y mypy strict sigue en verde sin plugin de SQLAlchemy (AC-11, AC-16)_
- [x] T6 @frontend-expert: Crear el shell de la app (`app/providers.tsx`, `app/router.tsx`, `app/theme.ts`, `api/queryClient.ts`, `layouts/RootLayout.tsx`, `constants/routes.ts`, `screens/NotFoundScreen/*`, `test/setup.ts`, `test/render.tsx` y los `.gitkeep`) con `HomeScreen` provisorio sin datos — _outcome: `vp test run` pasa `NotFoundScreen.test.tsx` vía `renderWithProviders`, y `src/` contiene los 11 directorios (AC-19, AC-20, AC-21, AC-27)_

### Wave 3 (depends on T4, T5)
- [x] T7 @backend-expert: Implementar `schemas/health.py`, `api/routes/health.py`, `api/router.py`, `main.py` (`create_app`, `lifespan`) y `scripts/export_openapi.py`, generar `backend/openapi.json` y agregar `tests/test_health.py`, `tests/test_openapi_export.py` y `tests/test_tooling.py` — _outcome: `uv run pytest`, `ruff` y `mypy` en verde; `GET /api/openapi.json` y `GET /api/health` responden 200 y `openapi.json` coincide con `app.openapi()` (AC-6, AC-10, AC-13, AC-14)_

### Wave 4 (depends on T6, T7)
- [x] T8 @frontend-expert: Crear `orval.config.ts` y `src/api/mutator.ts`, ejecutar `vp run generate:api`, conectar `HomeScreen` a `useGetHealth()` con estados de carga y error, y agregar `HomeScreen.test.tsx` — _outcome: `vp run generate:api` genera `src/api/generated/health/health.ts`; sin `openapi.json` sale con exit ≠ 0 nombrando la ruta; `vp check` y `vp test run` pasan; no hay `fetch(` fuera de `src/api/` (AC-23, AC-24, AC-25, AC-27, NFR-6)_
- [x] T9 @backend-expert: Crear `backend/Dockerfile` (targets `dev`, `builder` y `prod` con `--mount=type=ssh`) y `backend/.dockerignore` — _outcome: `docker build --ssh default --target prod backend` sale con exit 0, la imagen no tiene git, ssh ni claves, y sin agente SSH el build falla (AC-30, AC-34, NFR-3)_
- [x] T10 @frontend-expert: Crear `frontend/Dockerfile` (targets `dev`, `build` y `prod` nginx), `frontend/nginx.conf` y `frontend/.dockerignore` — _outcome: la imagen `prod` sirve `index.html` en :8080 sin Node y arranca aunque no exista el host `backend` (AC-30, AC-31)_

### Wave 5 (depends on T1, T8, T9, T10)
- [x] T11: Crear `docker-compose.dev.yml` y `docker-compose.prod.yml` — _outcome: cada modo levanta db, backend y frontend (dev con reload y HMR), `up backend`/`up frontend` levantan solo lo necesario, el volumen `pgdata` tiene nombre y sin `.env` falla con el mensaje de copiar `.env.example` (AC-29, AC-30, AC-31, AC-32, AC-33)_
- [x] T12 @frontend-expert: Crear `playwright.config.ts` y `e2e/home.spec.ts` (mock de `/api/health` con `page.route`, home y 404) — _outcome: `vp run e2e` sale con exit 0 (AC-28)_
- [x] T13 @docs-expert: Escribir `CLAUDE.md` (a partir de `future-plans/frontend-quality-prompt.md` + convenciones backend + flujo Orval) y `README.md` — _outcome: ambos archivos contienen todas las secciones listadas en "Docs changes" (AC-7, AC-10, AC-34, AC-35, AC-36, NFR-6)_

### Wave 6 (depends on T11, T12, T13)
- [x] T14: Ejecutar en un clon limpio cada comando del README en orden y los chequeos de la tabla Verification, midiendo los tiempos de los comandos de calidad — _outcome: todos los comandos salen con exit 0, cada comando de calidad tarda menos de 60 s y los desvíos quedan corregidos o registrados en Critical Decisions (AC-1, AC-3, AC-37, NFR-7)_
