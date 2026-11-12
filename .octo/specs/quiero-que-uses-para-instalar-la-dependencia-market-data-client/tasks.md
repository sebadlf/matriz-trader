# Tasks — Quiero que uses para instalar la dependencia market-data-client

### Wave 1

- [x] T1: Ejecutar `uv add --package matriz-worker "market-data-client @ git+https://github.com/gravity-quant/market-libs.git@market-data-client-v0.7.1#subdirectory=packages/market-data-client"` (toca solo `worker/pyproject.toml` y `uv.lock`) — _outcome: `uv run python -c "import market_data_client"` sale con 0 y `uv.lock` fija un SHA de 40 caracteres (AC-1, AC-2, AC-3, AC-4)_
- [x] T2: Instalar `git` y `ca-certificates` en `worker/Dockerfile` antes del primer `uv sync`, limpiando `/var/lib/apt/lists` — _outcome: el Dockerfile tiene el `RUN apt-get … git` antes de la línea `uv sync --frozen --no-install-workspace` (AC-9)_
- [x] T3: Agregar los campos `market_data_*` a `WorkerSettings` y el bloque `MARKET_DATA_*` comentado a `.env.example` — _outcome: `WorkerSettings` lee las 5 variables del `.env` raíz y `.env.example` las documenta con valores no secretos (AC-6)_
- [x] T4: Agregar la regla de market data en `## Convenciones` de `CLAUDE.md` y actualizar el bullet `worker/` — _outcome: `CLAUDE.md` contiene "El market data se obtiene siempre con `market-data-client`; nunca con `matriz-client`" con el módulo de acceso (AC-17, AC-19)_

### Wave 2 (depends on T1, T3)

- [x] T5: Crear `worker/src/worker/market_data_gateway.py` con `MarketDataGatewayError`, `Quote`, el `MarketDataGateway` Protocol y `MarketDataClientGateway`, y actualizar el docstring de `matriz_gateway.py` — _outcome: `uv run pyright` da 0 errores y es el único módulo que importa `market_data_client` (AC-8, AC-11, AC-12, AC-16)_
- [x] T6: Actualizar `worker/tests/test_settings.py` (limpieza de `MARKET_DATA_*`, mensajes de variables faltantes, test de lectura y test de exit 2 por variables de market data) — _outcome: `cd worker && uv run pytest tests/test_settings.py` pasa, incluido el caso de exit 2 por `MARKET_DATA_*` faltantes (AC-6, AC-7)_

### Wave 3 (depends on T5)

- [x] T7: Cablear `market_data` en `runner.run`/`serve` (connect, log, fallo → 1, cierre de ambos) y en `__main__.main` — _outcome: `uv run python -m worker` con `.env` válido loguea "market-data-client initialized" y sale con 0 con Ctrl+C (AC-13, AC-14)_
- [x] T8: Crear `worker/tests/test_market_data_gateway.py` con `httpx.MockTransport` y `max_retries=0` — _outcome: el test verifica que `httpx.ConnectError` se traduce a `MarketDataGatewayError` y que un health 200 no lanza (AC-12)_
- [x] T9: Documentar `market-data-client` en `worker/CLAUDE.md` (origen Git, actualización por tag, módulo, variables, regla, nota de repo privado, códigos de salida) — _outcome: `worker/CLAUDE.md` describe la librería y repite la regla junto a `matriz-client` (AC-5, AC-18, AC-19)_

### Wave 4 (depends on T7)

- [x] T10: Actualizar `worker/tests/test_runner.py` con `FakeMarketDataGateway`, las firmas nuevas y los tests de arranque OK, de fallo de market data y de fallo de Matriz sin conectar market data — _outcome: `cd worker && uv run pytest` pasa sin red y cubre el arranque exitoso y el fallo de inicialización con el fake (AC-13, AC-14, AC-15)_

### Wave 5 (depends on T2, T4, T6, T8, T9, T10)

- [x] T11: Correr `scripts/check.sh`, `docker compose build worker` y los greps de AC-2, AC-5, AC-11, AC-16 y AC-19 — _outcome: todos los gates salen con 0 y los greps dan los resultados esperados de `## Verification` (AC-2, AC-4, AC-5, AC-8, AC-9, AC-10, AC-11, AC-16, AC-19)_
