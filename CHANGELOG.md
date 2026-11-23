# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] - 2026-11-23

### Added

- Esqueleto del monorepo con los módulos `backend/` y `frontend/` y un único `.env` en la raíz (ignorado por git), documentado en `.env.example`.
- Backend en Python 3.13 con FastAPI, SQLAlchemy 2.0 async (PostgreSQL 17 + psycopg 3), pydantic-settings y uv, con `market-data-client` (`market-data-client-v0.7.1`) y `matriz-client` (`matriz-client-v0.4.0`) instaladas por SSH desde `gravity-quant/market-libs`.
- Endpoint `GET /api/health` y esquema OpenAPI versionado en `backend/openapi.json`, exportable con `uv run python -m app.scripts.export_openapi`.
- Validación de la configuración al arrancar: `python -m app` sale con código 1 y `Configuración inválida: <VARIABLE>` si falta una variable o es inválida.
- Calidad del backend: Ruff (con las reglas `ANN` sin excepciones), mypy `strict` con el plugin `pydantic.mypy` y pytest + pytest-asyncio + `httpx.AsyncClient`, incluido un test que detecta un `openapi.json` desactualizado.
- Frontend en React 19 + TypeScript `strict` sobre Vite+ (`vp`), con Ant Design 6, React Router 7, Zustand y TanStack Query, organizado en `app/`, `api/`, `screens/`, `components/`, `layouts/`, `hooks/`, `stores/`, `utils/`, `constants/`, `types/` y `test/`.
- Cliente de la API generado con Orval 8 (`vp run generate:api`, variante react-query) a partir de `backend/openapi.json`, con un único mutator `fetch` en `src/api/mutator.ts`.
- Pantalla de inicio que consulta `GET /api/health` y pantalla 404 para rutas desconocidas.
- Tests unitarios con `vp test` (Vitest + React Testing Library y el helper `renderWithProviders()`) y tests e2e con Playwright (`vp run e2e`), que mockean `/api/health` y no necesitan backend.
- Docker Compose en dos archivos independientes: `docker-compose.dev.yml` (recarga automática en backend y frontend) y `docker-compose.prod.yml` (imágenes sin herramientas de desarrollo y nginx que sirve el build y hace proxy de `/api`). Cada servicio se puede levantar por separado y PostgreSQL persiste en un volumen con nombre.
- `CLAUDE.md` con las convenciones, reglas de dependencia y comandos del proyecto, y `README.md` con la instalación y el uso.

### Notas

- Los `docker compose ... up --build` de ambos modos todavía no se verificaron de punta a punta (el daemon de Docker no pudo descargar imágenes en la máquina de verificación); `docker compose config` y el servicio `db` sí funcionan.
- `vp lint` y `vp check` muestran un warning conocido (`react/only-export-components` en `src/app/router.tsx`).
