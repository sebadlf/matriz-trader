# CLAUDE.md — backend

FastAPI (`matriz-backend`, paquete `backend`). Miembro del workspace `uv`; depende de `matriz-model` y `matriz-broker` (acceso a Matriz). El backend **no** importa `matriz_client`: todo pasa por `broker.matriz_gateway`.

## Archivos clave

- `src/backend/settings.py` — `BackendSettings` (`DATABASE_URL` obligatoria, `CORS_ORIGINS`, `LOG_LEVEL`; opcionales `MATRIZ_BASE_URL`, `MATRIZ_USERNAME`, `MATRIZ_PASSWORD` y `MATRIZ_ACCOUNTS` — lista separada por comas, expuesta como `matriz_account_list` sin espacios, vacíos ni duplicados) y `load_settings()`, que sale con código 2 y `Missing required environment variables: ...` si falta alguna.
- `src/backend/main.py` — `create_app(settings, trading=None)`: registra `health` y `trading`; CORS con `allow_methods=["GET", "POST"]`; en tests se pasa un `FakeTrading` como `trading`. `app` se construye al pedirlo (`__getattr__` de módulo), así que importar el módulo no exige `.env`.
- `src/backend/health.py` — `GET /health` (`operation_id="getHealth"`): 200 `{"status":"ok","database":"ok"}` o 503 `{"status":"degraded","database":"unavailable"}`. `DatabaseStatusTracker` loguea `ERROR` al pasar a unavailable (causa del driver, sin contraseña) e `INFO` al recuperarse; el cuerpo de la respuesta nunca incluye el error.
- `src/backend/matriz.py` — una `MatrizClientGateway` por proceso (login diferido al primer request, así `/health` no depende de Matriz), `InstrumentCache` en memoria (TTL 1 h, no cachea fallos), dependencias `get_trading`/`get_instrument_cache`/`get_accounts` y traducción de errores.
- `src/backend/trading.py` — endpoints de órdenes (todos `def` síncronos, cuerpo de error `{"detail": ...}`):

  | Método y path | `operation_id` | Respuesta |
  |---|---|---|
  | `GET /accounts` | `listAccounts` | `200 {"accounts": [...]}` (orden de `MATRIZ_ACCOUNTS`; `[]` si vacío) |
  | `GET /instruments` | `listInstruments` | `200 [{symbol, market_id}]` (cacheado) |
  | `GET /orders?account_id=` | `listOrders` | `200 [OrderOut]` vía `get_all_orders`, por `transact_time` descendente |
  | `POST /orders` | `createOrder` | `201 {cl_ord_id, proprietary}`; `NewOrderRequest` exige `quantity` entera > 0, `price` solo en `LIMIT` |
  | `POST /orders/cancel` | `cancelOrder` | `200 {cl_ord_id, proprietary}` |

  Errores: `GatewayError` → `502 "Matriz: <mensaje sin secretos>"`; sin `MATRIZ_USERNAME`/`MATRIZ_PASSWORD` → `503`; `account_id` fuera de `MATRIZ_ACCOUNTS` → `422 "Cuenta no configurada: <id>"`; validación → `422` estándar.
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
uv run pytest                 # sin Postgres ni Matriz: dependency_overrides, settings armadas a mano y tests/fake_trading.py
```

`tests/test_openapi_snapshot.py` falla si `frontend/openapi.json` está desactualizado.
