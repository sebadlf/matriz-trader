# CLAUDE.md — worker

Proceso long-running (`matriz-worker`, paquete `worker`) que inicializa `matriz-client` 0.3.0 y `market-data-client` 0.7.1, y queda vivo hasta SIGINT/SIGTERM.

- `matriz-client` — solo autenticación/conexión contra Matriz. Viene del wheel de GitHub Releases declarado en `[tool.uv.sources]` de `pyproject.toml`. **No se usa para market data.**
- `market-data-client` — única fuente de market data. Viene de Git: monorepo público `gravity-quant/market-libs`, `subdirectory = "packages/market-data-client"`, ref en el tag `market-data-client-v0.7.1`; `uv.lock` fija el SHA del commit. Módulo importable: `market_data_client` (publica `py.typed`, no necesita stubs).

**Regla:** el market data se obtiene siempre con `market-data-client`; nunca con `matriz-client`. Único punto de acceso: `src/worker/market_data_gateway.py` (ningún otro módulo importa `market_data_client`).

### Actualizar `market-data-client`

Cambiar de tag con `uv add`, nunca editando `pyproject.toml` ni `uv.lock` a mano. Desde la raíz, siempre con `--package` (sin él la dependencia termina en el `pyproject.toml` raíz):

```bash
uv add --package matriz-worker \
  "market-data-client @ git+https://github.com/gravity-quant/market-libs.git@market-data-client-vX.Y.Z#subdirectory=packages/market-data-client"
```

### Repo privado (hoy no aplica)

`market-libs` es público: `uv sync` y el build de Docker no necesitan credenciales (el `Dockerfile` solo instala `git` y `ca-certificates`). Si pasara a privado, mantener la URL `https://` en `pyproject.toml` y autenticar por fuera de los archivos versionados:

- Local: agente SSH con acceso al repo y `git config --global url."git@github.com:".insteadOf "https://github.com/"`.
- Docker: instalar `openssh-client`, aplicar el mismo `insteadOf` dentro del build y correr `uv sync` con `RUN --mount=type=ssh` (`docker compose build --ssh default worker`).
- Nunca poner tokens en `pyproject.toml`, `uv.lock`, `Dockerfile` ni `.env.example`.

## Archivos clave

- `src/worker/settings.py` — `WorkerSettings`: `MATRIZ_BASE_URL`, `MATRIZ_USERNAME`, `MATRIZ_PASSWORD`, `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE`, `MARKET_DATA_AUTH0_TOKEN_URL` (obligatorias); `MARKET_DATA_BASE_URL` (default: API de develop), `WORKER_HEARTBEAT_SECONDS`, `LOG_LEVEL`.
- `src/worker/matriz_gateway.py` — único módulo que importa `matriz_client`. `connect()` llama a `Client.login()` y traduce los errores a `GatewayError`. Solo autenticación/conexión, no market data.
- `src/worker/market_data_gateway.py` — único módulo que importa `market_data_client`. Expone el `Protocol` `MarketDataGateway` (`connect`, `get_quote`, `close`), el tipo propio `Quote` y `MarketDataClientGateway`; traduce los errores de la librería a `MarketDataGatewayError`. `connect()` llama a `get_health()`, que es anónimo: valida conectividad y URL, no las credenciales Auth0.
- `src/worker/runner.py` — `run()` (connect Matriz → connect market data → loop de heartbeat → close de ambos) y `serve()` (handlers de señales).
- `src/worker/__main__.py` — `main(env_file)`: código 2 si falta configuración (incluidas las `MARKET_DATA_*` obligatorias), 1 si falla la conexión a Matriz o a market data, 0 al detenerse.

## Comandos

Desde la raíz del repo:

```bash
uv run python -m worker       # Ctrl+C para detenerlo (sale con 0)
uv run pyright                # strict, sin argumentos: `uv run pyright worker` sale 0 aunque haya errores
```

Desde `worker/`:

```bash
uv run pytest                 # con fakes de ambos gateways: no necesita red ni credenciales
```

Con las credenciales `changeme` de `.env.example` el login de Matriz devuelve 401 y el worker sale con 1; en Compose queda `exited` tras `restart: on-failure:3`. Las credenciales `MARKET_DATA_*` inválidas no hacen fallar el arranque (el health check es anónimo): el error aparece recién en la primera llamada autenticada.
