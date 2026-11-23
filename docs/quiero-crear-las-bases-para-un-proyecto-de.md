# Bases del proyecto (setup inicial)

Primera etapa de `matriz-trader`: deja armado el esqueleto del monorepo, sin lógica de negocio. La instalación y los comandos están en [`README.md`](../README.md) y las convenciones en [`CLAUDE.md`](../CLAUDE.md); este documento resume qué se construyó y por qué.

## Qué incluye

| Parte | Contenido |
|---|---|
| Raíz | Un único `.env` (ignorado por git) que leen backend, frontend y Docker Compose; `.env.example` documenta cada variable. |
| `backend/` | Python 3.13 + FastAPI + uv, SQLAlchemy 2.0 async contra PostgreSQL 17, `Settings` de pydantic-settings, `GET /api/health` y `openapi.json` versionado. Ruff (`ANN`), mypy `strict` y pytest. |
| `frontend/` | React 19 + TypeScript sobre Vite+ (`vp`), Ant Design 6, React Router 7, Zustand y un cliente Orval 8 (react-query). Pantalla de inicio que consulta `/api/health` y pantalla 404. Vitest + RTL y Playwright. |
| Docker | `docker-compose.dev.yml` y `docker-compose.prod.yml`, independientes. En producción, nginx sirve el build y hace proxy de `/api` al backend. |

## Flujo del contrato backend → frontend

1. Se cambian los endpoints en `backend/app/api/routes/` (con `operation_id` explícito).
2. `uv run python -m app.scripts.export_openapi` escribe `backend/openapi.json` sin levantar el servidor ni conectarse a la base.
3. `vp run generate:api` genera `frontend/src/api/generated/` a partir de ese archivo, así que no hace falta el backend en ejecución.
4. Se commitean juntos `openapi.json` y el código generado. `backend/tests/test_openapi_export.py` falla si el archivo quedó desactualizado.

## Decisiones principales

- **Endpoint mínimo**: `GET /api/health` devuelve solo el estado del servicio, sin chequear la base. Alcanza para validar el pipeline Orval → frontend → Playwright, y los tests e2e no dependen de PostgreSQL.
- **OpenAPI versionado**: Orval lee `backend/openapi.json` y no un backend en ejecución, para que la generación sea reproducible. Si el archivo falta, `generate:api` termina con error e indica la ruta.
- **Sin Alembic por ahora**: se configura junto con el primer modelo de dominio.
- **Frontend en producción con nginx**: servirlo desde FastAPI acoplaría las imágenes, y `vp preview` es un servidor de desarrollo.
- **Dos archivos de Compose**: cada modo se lee de forma independiente; la duplicación de PostgreSQL y los volúmenes es un costo menor.
- **Tests del backend**: pytest + pytest-asyncio con `httpx.AsyncClient` sobre `ASGITransport`, sin ejecutar el `lifespan` ni requerir PostgreSQL.
- **Instalación de `vp`**: con el instalador oficial (`curl -fsSL https://vite.plus | bash`). Con `npm install -g vite-plus`, `vp test run` no encuentra `jsdom`.

## Limitaciones conocidas

- Los `docker compose ... up --build` de ambos modos (y el build del backend con `--ssh default`) aún no se verificaron de punta a punta: el daemon de Docker de la máquina de verificación no pudo descargar imágenes. `docker compose config`, el error sin `.env` y el servicio `db` sí se verificaron.
- No exportes `NODE_ENV=production` en la shell al correr `vp test`: React carga su build de producción y los tests fallan con `React.act is not a function`.
- `vp lint` y `vp check` muestran un warning de `react/only-export-components` en `src/app/router.tsx`.
