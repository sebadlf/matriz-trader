# CLAUDE.md — worker

Proceso long-running (`matriz-worker`, paquete `worker`) que inicializa `matriz-client` 0.3.0 y queda vivo hasta SIGINT/SIGTERM. `matriz-client` viene del wheel de GitHub Releases declarado en `[tool.uv.sources]` de `pyproject.toml`.

## Archivos clave

- `src/worker/settings.py` — `WorkerSettings`: `MATRIZ_BASE_URL`, `MATRIZ_USERNAME`, `MATRIZ_PASSWORD` (obligatorias), `WORKER_HEARTBEAT_SECONDS`, `LOG_LEVEL`.
- `src/worker/matriz_gateway.py` — único módulo que importa `matriz_client`. `connect()` llama a `Client.login()` y traduce los errores a `GatewayError`.
- `src/worker/runner.py` — `run()` (connect → loop de heartbeat → close) y `serve()` (handlers de señales).
- `src/worker/__main__.py` — `main(env_file)`: código 2 si falta configuración, 1 si falla la conexión a Matriz, 0 al detenerse.

## Comandos

Desde la raíz del repo:

```bash
uv run python -m worker       # Ctrl+C para detenerlo (sale con 0)
uv run pyright                # strict, sin argumentos: `uv run pyright worker` sale 0 aunque haya errores
```

Desde `worker/`:

```bash
uv run pytest                 # con FakeGateway: no necesita red ni credenciales
```

Con las credenciales `changeme` de `.env.example` el login devuelve 401 y el worker sale con 1; en Compose queda `exited` tras `restart: on-failure:3`.
