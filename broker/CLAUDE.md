# CLAUDE.md — broker

Paquete `matriz-broker` (`import broker`, layout `src/`, `py.typed`). Miembro del workspace `uv`; lo usan `matriz-backend` (órdenes) y `matriz-worker` (login al arrancar).

**Regla:** Matriz se accede siempre con `matriz-client` 0.3.0, que se declara **solo** en `broker/pyproject.toml` (wheel de GitHub Releases en `[tool.uv.sources]`). Único punto de acceso: `src/broker/matriz_gateway.py`; ningún otro módulo del repo importa `matriz_client`. `matriz-client` no se usa para market data (eso es `worker/src/worker/market_data_gateway.py`). `get_all_instruments` se considera metadata para el alta de órdenes, no market data.

Comprobación: `rg -l "matriz_client" --glob '*.py' backend worker broker model e2e` debe devolver solo `broker/src/broker/matriz_gateway.py`.

## Archivos clave

- `src/broker/matriz_gateway.py` — expone tipos propios del repo (`MatrizCredentials`, `InstrumentRef`, `OrderRecord`, `NewOrder`, `OrderAck`, `GatewayError`), nunca modelos de la librería:
  - `Protocol` `MatrizGateway` (`connect`, `close`) — sesión; lo usa el worker.
  - `Protocol` `MatrizTrading` (`list_orders` → `get_all_orders`, `new_order`, `cancel_order`, `list_instruments`) — operación; lo usa el backend.
  - `MatrizClientGateway(credentials)` implementa ambos. Construirlo no hace I/O; credenciales siempre explícitas (con `None` la librería cae a `PRIMARY_*` del entorno). Login diferido y único, protegido por `threading.Lock`; ante `AuthenticationError` el próximo uso reintenta el login.
  - `new_order` solo pasa `order_type` y `market_id` como kwargs (`price=None` en `MARKET`); `time_in_force`, `iceberg`, `display_qty`, `cancel_previous` y `expire_date` quedan con el default de la librería.
  - `MatrizClientError | httpx.HTTPError` → `GatewayError` con la contraseña reemplazada por `***`. Respuesta sin `clientId`/`proprietary` → `GatewayError`.

## Comandos

Desde `broker/`:

```bash
uv run pytest                 # con un Client falso: no necesita red ni credenciales
```

Desde la raíz: `uv run pyright` (strict, sin argumentos). `scripts/check.sh` corre los tests de `broker`.
