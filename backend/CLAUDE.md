# CLAUDE.md — backend

FastAPI (`matriz-backend`, paquete `backend`). Miembro del workspace `uv`; depende de `matriz-model`.

## Archivos clave

- `src/backend/settings.py` — `BackendSettings` (`DATABASE_URL` obligatoria, `CORS_ORIGINS`, `LOG_LEVEL`) y `load_settings()`, que sale con código 2 y `Missing required environment variables: ...` si falta alguna.
- `src/backend/main.py` — `create_app(settings)`. `app` se construye al pedirlo (`__getattr__` de módulo), así que importar el módulo no exige `.env`.
- `src/backend/health.py` — `GET /health` (`operation_id="getHealth"`): 200 `{"status":"ok","database":"ok"}` o 503 `{"status":"degraded","database":"unavailable"}`. `DatabaseStatusTracker` loguea `ERROR` al pasar a unavailable (causa del driver, sin contraseña) e `INFO` al recuperarse; el cuerpo de la respuesta nunca incluye el error.
- `src/backend/export_openapi.py` — escribe `frontend/openapi.json` sin levantar el servidor.

## Comandos

Desde la raíz del repo:

```bash
docker compose up postgres                               # BD para dev
uv run uvicorn backend.main:app --reload --port 8000     # http://localhost:8000/health
uv run python -m backend.export_openapi                  # tras cambiar la API; commitear frontend/openapi.json
uv run pyright                                           # strict, siempre sin argumentos
```

Desde `backend/`:

```bash
uv run pytest                 # sin Postgres: usa dependency_overrides y settings armadas a mano
```

`tests/test_openapi_snapshot.py` falla si `frontend/openapi.json` está desactualizado.
