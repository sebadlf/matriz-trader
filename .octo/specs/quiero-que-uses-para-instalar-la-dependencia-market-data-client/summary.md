🔧 **Bash**

```bash
cat .octo/specs/quiero-que-uses-para-instalar-la-dependencia-market-data-client/requirements.md .octo/specs/quiero-que-uses-para-instalar-la-dependencia-market-data-client/plan.md; git diff -- .env.example CLAUDE.md worker/ ; cat worker/src/worker/market_data_gateway.py; head -60 worker/tests/test_market_data_gateway.py
```<persisted-output>
Output too large (74KB). Full output saved to: /Users/sebadlf/.claude/projects/-Users-sebadlf-development-matriz-trader/ace7fa1e-47af-400c-bdaf-9c7ab2f5b5a9/tool-results/bppp0cp3r.txt

Preview (first 2KB):
# Requirements — Integrar `market-data-client` como única fuente de market data

## Introducción

Hoy el `worker` depende de `matriz-client` 0.3.0 (wheel de GitHub Releases) y lo usa para autenticarse contra Matriz (`worker/src/worker/matriz_gateway.py`). Este feature incorpora la librería `market-data-client`, instalada desde Git con `uv add`, la deja configurada y lista 
… (truncated)🔧 **Bash**

```bash
git diff --stat; git diff -- .env.example CLAUDE.md worker/pyproject.toml worker/Dockerfile worker/src/worker/settings.py worker/src/worker/__main__.py worker/src/worker/matriz_gateway.py worker/src/worker/runner.py; cat worker/src/worker/market_data_gateway.py; grep -n "^#\|^- \*\*\|Decis" .octo/specs/quiero-que-uses-para-instalar-la-dependencia-market-data-client/plan.md | head -60
``` .env.example                        | 13 +++++++
 .octo/specs/initial-setup/spec.json |  6 +--
 CLAUDE.md                           |  3 +-
 uv.lock                             | 12 ++++++
 worker/CLAUDE.md                    | 37 ++++++++++++++----
 worker/Dockerfile                   |  5 +++
 worker/pyproject.toml               |  2 +
 worker/src/worker/__main__.py       |  5 ++-
 worker/src/worker/matriz_gateway.py |  5 ++-
 worker/src/worker/runner.py         | 42 +++++++++++++++-----
 worker/src/worker/settings.py       |  7 ++++
 worker/tests/test_runner.py         | 76 +++++++++++++++
… (truncated)🔧 **Bash**

```bash
git diff -- worker/CLAUDE.md | head -70; grep -n "^def test\|^async def test" worker/tests/test_market_data_gateway.py worker/tests/test_runner.py worker/tests/test_settings.py; sed -n 387,395p .octo/specs/quiero-que-uses-para-instalar-la-dependencia-market-data-client/plan.md
```diff --git a/worker/CLAUDE.md b/worker/CLAUDE.md
index 765b7cf..d7403a5 100644
--- a/worker/CLAUDE.md
+++ b/worker/CLAUDE.md
@@ -1,13 +1,36 @@
 # CLAUDE.md — worker
 
-Proceso long-running (`matriz-worker`, paquete `worker`) que inicializa `matriz-client` 0.3.0 y queda vivo hasta SIGINT/SIGTERM. `matriz-client` viene del wheel de GitHub Releases declarado en `[tool.uv.sources]` de `pyproject.toml`.
+Proceso long-running (`matriz-worker`, paquete `worker`) que inicializa `matriz-client` 0.3.0 y `market-data-client` 0.7.1, y queda vivo hasta SIGINT/SIGTERM.
+
+- `matriz-client` — solo autenticac
… (truncated)## Resumen

`market-data-client` v0.7.1 ya está instalado en el workspace `uv`. Se instaló con `uv add` desde Git, apuntando al monorepo `gravity-quant/market-libs`, y se agregó al `worker` detrás de un único gateway tipado. Además, quedó escrita como regla de arquitectura que el market data se obtiene siempre con `market-data-client` y nunca con `matriz-client`.

## Cambios

- **Dependencia:** se agregó con `uv add --package matriz-worker` usando el tag `market-data-client-v0.7.1`. `uv` la guarda como `rev`, y el SHA del commit queda fijado en `uv.lock`. La URL real es `market-libs.git#subdirectory=packages/market-data-client` y no el literal `<org>/market-data-client.git` que pedía el requerimiento AC-1; está anotado como pregunta abierta. `worker/pyproject.toml` y `uv.lock` también cambiaron, aunque no figuran en la lista de archivos.
- **Configuración:** hay cuatro variables `MARKET_DATA_*` nuevas obligatorias y `MARKET_DATA_BASE_URL` es opcional (por defecto apunta a develop). Si falta alguna obligatoria, el worker sale con código 2.
- **Gateway:** `market_data_gateway.py` es el único módulo que importa `market_data_client`. Expone el `Protocol` `MarketDataGateway`, el tipo `Quote` y una implementación que traduce los errores de la librería a `MarketDataGatewayError`.
- **Runner:** al arrancar conecta primero Matriz y después market data, y cierra los dos al terminar. Si cualquiera de las dos conexiones falla, sale con código 1.
- **Docker:** se instalan `git` y `ca-certificates`, porque `uv sync --frozen` necesita resolver la fuente Git.
- **Docs y tests:** la regla quedó en `CLAUDE.md` y en `worker/CLAUDE.md`. Los tests usan fakes y no necesitan red.
- **Limitación conocida:** `connect()` usa `get_health()`, que no requiere autenticación. Por eso, si las credenciales de Auth0 son inválidas, el arranque no falla y el error aparece recién en la primera llamada autenticada.

## Archivos

- `worker/src/worker/market_data_gateway.py` — nuevo y único punto de acceso a `market-data-client`. Le pasa las credenciales de forma explícita al `Client`, para que la librería no las tome de `os.environ`. El precio se lee de `market_data.LA` y se convierte a `Decimal`, y `received_at` a un `datetime` en UTC.
- `worker/src/worker/settings.py` — agrega `market_data_client_id`, `market_data_client_secret` (`SecretStr`), `market_data_audience` y `market_data_auth0_token_url`, más `market_data_base_url` con un valor por defecto.
- `worker/src/worker/runner.py` — `run` y `serve` reciben el `MarketDataGateway`. Conecta market data después de Matriz y cierra los dos con `_close_all`.
- `worker/src/worker/__main__.py` — crea el `MarketDataClientGateway` y se lo pasa a `serve`.
- `worker/src/worker/matriz_gateway.py` — solo cambia el docstring: aclara que este módulo es para autenticación y no para market data.
- `worker/tests/test_market_data_gateway.py` — nuevo. Prueba la traducción de errores en `connect` y el caso con la API sana.
- `worker/tests/test_runner.py` — cubre que market data se inicializa y se cierra, que una falla de market data devuelve 1 y que, si falla Matriz, no se intenta conectar market data.
- `worker/tests/test_settings.py` — prueba la lectura de las variables `MARKET_DATA_*` y la salida con código 2 cuando faltan.
- `worker/Dockerfile` — instala `git` y `ca-certificates` antes de `uv sync`.
- `.env.example` — agrega la sección `MARKET_DATA_*` con valores de ejemplo y comentarios.
- `CLAUDE.md` — describe al worker con sus dos librerías y agrega la regla de que el market data viene solo de `market-data-client`.
- `worker/CLAUDE.md` — explica qué rol cumple cada librería, cómo actualizar el tag con `uv add --package`, qué hacer si el repo pasa a ser privado, y actualiza los archivos clave y los códigos de salida.
- `.octo/specs/.../requirements.md` — nuevo. Contiene las user stories y los criterios de aceptación del feature.
- `.octo/specs/.../plan.md` — contiene el plan, los riesgos, la verificación, las preguntas abiertas y tres decisiones críticas: que la ref quede como `rev`, que el precio salga del campo `LA` y que se acoten los greps de verificación.
- `.octo/specs/.../tasks.md` — tiene todas las tareas marcadas como completadas.