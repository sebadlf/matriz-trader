🔧 **Bash**

```bash
head -c 6000 .octo/specs/quiero-crear-las-bases-para-un-proyecto-de/requirements.md; echo ----; head -c 9000 .octo/specs/quiero-crear-las-bases-para-un-proyecto-de/plan.md
```# Requirements: Bases del proyecto matriz-trader (setup inicial)

## Introduction

`matriz-trader` será un cliente de trading que consume las librerías internas `market-data-client` (v0.7.1) y `matriz-client` (v0.4.0) del repositorio `gravity-quant/market-libs`. Esta primera etapa **solo** establece el esqueleto del monorepo — un módulo `backend/` (Python 3.13 + FastAPI) y un módulo `frontend/` (React + TypeScript + Vite+) — junto con PostgreSQL, Docker Compose para dev y producción, un único `.env` en la raíz, y la documentación `CLAUDE.md` y `README.md`. No se implementa ninguna funcionalida
… (truncated)🔧 **Bash**

```bash
cat .env.example; echo ----; head -60 docker-compose.dev.yml; echo ----; cat frontend/src/api/mutator.ts; echo ----; cat backend/app/core/config.py | head -70; echo ----; grep -n "def test" backend/tests/test_db.py backend/tests/test_config.py; echo ----; cat .octo/specs/quiero-crear-las-bases-para-un-proyecto-de/tasks.md | head -60
```# =====================================================================
# matriz-trader — variables de entorno
# Copiá este archivo a `.env` en la raíz del repo: `cp .env.example .env`
# Es el ÚNICO .env del proyecto: lo leen backend, frontend y Docker Compose.
# Los valores de ejemplo NO son secretos; cambialos en tu `.env` local.
# =====================================================================

# --- PostgreSQL (lo usan los servicios db de compose) ---
# Usuario que crea la imagen de Postgres al inicializar el volumen.
POSTGRES_USER=matriz
# Contraseña de ese usuario (solo para desarr
… (truncated)🔧 **Bash**

```bash
grep -n -A30 "Critical Decisions" .octo/specs/quiero-crear-las-bases-para-un-proyecto-de/plan.md | tail -40; echo ----; head -30 frontend/Dockerfile; grep -n "location\|proxy_pass\|resolver" frontend/nginx.conf; grep -n "def \|Base\b" backend/app/db/session.py backend/app/db/base.py | head
```584-
585-## Open Questions
586-
587-- [ ] Las dos librerías traen un `.env.example` propio (credenciales Auth0/Primary). Como no se usan en esta etapa, sus variables **no** se agregan al `.env.example` raíz. Revisitar cuando se implemente la primera integración.
588-- [ ] El e2e usa un mock de `/api/health` con `page.route` y no golpea el backend real. ¿Agregamos más adelante un proyecto de Playwright contra `docker-compose.dev.yml`?
589-- [ ] Elegí pnpm como gestor de paquetes del frontend (lockfile `frontend/pnpm-lock.yaml`). Si Vite+ recomienda otro por defecto, T3 lo ajusta y lo registra.

… (truncated)## Overview

Se armó el esqueleto del monorepo `matriz-trader`: un `backend/` en Python 3.13 + FastAPI con un solo endpoint (`GET /api/health`), un `frontend/` en React + TypeScript + Vite+ que habla con el backend solo a través de Orval, PostgreSQL, Docker Compose para dev y prod, y un único `.env` en la raíz. No hay lógica de negocio. El objetivo es que cualquiera pueda clonar el repo, configurar el `.env`, levantar cada parte y tener lint, tipado y tests en verde desde el primer commit.

## Changes

- **Configuración raíz:** un único `.env` en la raíz, ignorado por git. `.env.example` documenta cada variable con un comentario y un valor de ejemplo no secreto.
- **Backend:** `Settings` tipado con pydantic-settings, que lee el `.env` de la raíz y aborta con exit 1 nombrando la variable inválida (`Configuración inválida: <VAR>`). Capa de base de datos con SQLAlchemy 2.0 async (`Base`, `TimestampMixin`, engine, fábrica de sesiones y `get_session`), sin modelos de dominio. Las dos librerías de `gravity-quant/market-libs` se instalan por SSH, fijadas por tag.
- **Frontend:** toolchain de Vite+ (`vp`) con TypeScript strict y alias `@/`. `envDir` apunta a la raíz. El dev server hace proxy de `/api` al backend. El cliente Orval (react-query) se genera desde el archivo versionado `backend/openapi.json`, y `fetch` aparece solo en el mutator (`customFetch`, que lanza `ApiError`). `HomeScreen` consume `useGetHealth()` y maneja los estados de carga y error.
- **Docker:** Dockerfiles multi-stage. El build del backend usa SSH. La imagen prod del frontend es nginx sin Node, con fallback de SPA y proxy de `/api/` resuelto en tiempo de ejecución, así que arranca aunque el host `backend` no exista. Hay dos archivos compose independientes (`dev` con reload y HMR, `prod` con nginx), cada uno con `db`, `backend` y `frontend`, y un volumen `pgdata` con nombre. Si falta el `.env`, compose falla con un mensaje que dice cómo crearlo.
- **Documentación:** `CLAUDE.md` reúne convenciones, reglas de dependencias, flujo de contrato con Orval y definición de "terminado". `README.md` cubre la instalación (incluido el requisito de acceso SSH) y el uso.
- **Decisiones registradas en el plan:** las librerías quedaron en versiones más nuevas que las que asumía el plan (antd 6, Orval 8). React Router quedó en 7 y jsdom en 29 para seguir funcionando con Node 22.20. Se agregó un `pnpm-workspace.yaml`, que pnpm 12 necesita para los overrides y para aprobar el build de `esbuild`. Además, `vp test` falla si la shell exporta `NODE_ENV=production`.

## Files

- `README.md`: guía de instalación y uso (acceso SSH a market-libs, URL del OpenAPI, comandos de cada módulo y de Docker Compose).
- `CLAUDE.md`: guía para agentes y desarrolladores con stack, estructura de carpetas, reglas de dependencias, flujo de Orval, convenciones, tests y definición de "terminado".
- `docker-compose.dev.yml`: `db` (Postgres 17), `backend` (target `dev`, código montado y `--reload`) y `frontend` (`vp dev` con HMR), con guards `:?` si falta el `.env`.
- `docker-compose.prod.yml`: `db`, `backend` (target `prod`) y `frontend` servido por nginx.
- `.gitignore`: ignora `.env` y `.env.*` (salvo `.env.example`), entornos virtuales, caches, `node_modules`, `dist` y los reportes de Playwright.
- `.env.example`: variables de Postgres, backend y frontend, cada una comentada.
- `frontend/Dockerfile`: stages `deps`, `dev`, `build` y `prod` (nginx-unprivileged en :8080).
- `frontend/nginx.conf`: fallback de SPA, caché de `/assets/` y proxy de `/api/` al backend con resolver dinámico.
- `frontend/.dockerignore`: deja fuera del contexto de build las dependencias, los artefactos y el `.env`.
- `frontend/orval.config.ts`: cliente `react-query` con `httpClient: 'fetch'`, modo `tags-split`, mutator `customFetch` e input `../backend/openapi.json`.
- `frontend/src/api/mutator.ts`: único punto con `fetch`. Parsea el body y lanza `ApiError` cuando la respuesta no es `ok`.
- `frontend/src/screens/HomeScreen/HomeScreen.tsx`: muestra el estado de salud del backend con `useGetHealth()`.
- `frontend/src/screens/HomeScreen/HomeScreen.test.tsx`: tests de carga, éxito y error, mockeando `fetch` en el borde.
- `frontend/src/main.tsx`: monta `<AppProviders><AppRouter/></AppProviders>`.
- `frontend/src/vite-env.d.ts`: tipos de cliente de Vite+.
- `frontend/index.html`: HTML de entrada de la SPA.
- `frontend/tsconfig.json`: TypeScript strict para `src/` con alias `@/*`.
- `frontend/tsconfig.node.json`: tsconfig de los archivos de config (Vite, Orval, Playwright).
- `frontend/vite.config.ts`: única config de Vite, lint, formato y tests, con alias, `envDir` en la raíz, proxy de `/api` e `ignorePatterns` para `generated/`.
- `frontend/pnpm-workspace.yaml`: override de `vite` hacia Vite+ y aprobación del build de `esbuild` para pnpm 12.
- `frontend/package.json`: dependencias (React 19, antd 6, Orval 8, React Router 7, Zustand, TanStack Query, Playwright) y los scripts `generate:api` y `e2e`.
- `backend/Dockerfile`: targets `dev`, `builder` y `prod`. Instala las librerías privadas con `RUN --mount=type=ssh`, sin dejar git, ssh ni claves en la imagen final.
- `backend/.dockerignore`: excluye `.venv`, `.env` y caches.
- `backend/app/__main__.py`: entrypoint `python -m app [--reload]` que valida la configuración antes de levantar uvicorn.
- `backend/app/core/config.py`: `Settings`, `load_settings()` (exit 1 nombrando la variable) y `get_settings()` cacheado.
- `backend/app/db/base.py`: `Base` declarativa con convención de nombres y `TimestampMixin` con `Mapped[...]`.
- `backend/app/db/session.py`: `build_engine()`, `build_session_factory()` y la dependencia `get_session`.
- `backend/tests/conftest.py`: fixture autouse `test_env`, que define un `DATABASE_URL` de prueba.
- `backend/tests/test_config.py`: carga desde el `.env`, ruta del `.env` raíz y salida con error ante `DATABASE_URL` o `BACKEND_PORT` inválidos.
- `backend/tests/test_db.py`: verifica que no haya modelos de negocio, que el mixin use anotaciones tipadas con timezone y que el engine y las sesiones apunten a Postgres.
- `.octo/specs/.../requirements.md`: user stories y criterios de aceptación EARS del setup.
- `.octo/specs/.../plan.md`: enfoque, archivos afectados, verificación y las decisiones críticas tomadas durante la implementación.
- `.octo/specs/.../tasks.md`: las tareas T1–T14 marcadas como completadas.