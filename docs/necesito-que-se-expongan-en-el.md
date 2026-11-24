# Configuración de `matriz-client` y `market-data-client`

El backend expone en el `.env` de la raíz las ocho variables que leen las librerías internas `matriz-client` y `market-data-client`. Todavía no construye ningún cliente: esta etapa solo deja la configuración documentada, tipada y validada al arrancar. La instalación está en [`README.md`](../README.md).

## Variables

| Librería | Variable | Obligatoria | Tipo en `Settings` | Default |
|---|---|---|---|---|
| `matriz-client` | `PRIMARY_USER` | sí | `str` no vacío | — |
| `matriz-client` | `PRIMARY_PASSWORD` | sí | `SecretStr` no vacío | — |
| `matriz-client` | `PRIMARY_BASE_URL` | no | `HttpUrl` | `https://api.remarkets.primary.com.ar` (reMarkets) |
| `market-data-client` | `MARKET_DATA_CLIENT_ID` | sí | `str` no vacío | — |
| `market-data-client` | `MARKET_DATA_CLIENT_SECRET` | sí | `SecretStr` no vacío | — |
| `market-data-client` | `MARKET_DATA_AUDIENCE` | sí | `str` no vacío | — |
| `market-data-client` | `MARKET_DATA_AUTH0_TOKEN_URL` | sí | `HttpUrl` | — |
| `market-data-client` | `MARKET_DATA_BASE_URL` | no | `HttpUrl` | `https://market-data-develop.bbsa.com.ar/api` |

Los nombres son exactamente los que leen las librerías, así que `Settings` y la librería leen el mismo valor sin alias. `.env.example` trae placeholders que permiten arrancar en local; Docker Compose las entrega al contenedor por `env_file: .env`, sin redefinirlas en `environment:`.

## Comportamiento al arrancar

- Si falta una credencial, está vacía o solo tiene espacios, o si una URL no es `http`/`https` absoluta, `python -m app` (y `alembic`, que también llama a `load_settings()`) sale con código 1:

  ```text
  Configuración inválida: PRIMARY_BASE_URL, MARKET_DATA_CLIENT_SECRET
    - PRIMARY_BASE_URL: URL scheme should be 'http' or 'https'
    - MARKET_DATA_CLIENT_SECRET: Field required
  ```

- El mensaje nunca incluye el valor recibido ni el traceback encadenado, así que los secretos no llegan a stderr.
- Con la configuración válida, el `lifespan` registra `external_endpoints` con `primary_host`, `market_data_host` y `market_data_auth_host`: solo hosts, nunca usuario, secretos ni URL completa.
- `PRIMARY_PASSWORD` y `MARKET_DATA_CLIENT_SECRET` aparecen enmascarados en `repr()`/`str()` de `Settings` y en los logs de structlog.

## Decisiones principales

- **Credenciales obligatorias**: el error aparece al arrancar y no al primer uso del cliente. Como consecuencia, los tests (`test_env` en `backend/tests/conftest.py`) y el job `migrations` de CI definen valores ficticios.
- **«Todo o nada» por librería sin validador extra**: como las seis credenciales son obligatorias, pydantic ya nombra cada variable faltante del grupo.
- **Campos planos, no submodelos**: `settings.primary_user` en lugar de `settings.matriz.user`, para no tener que renombrar las variables ni sumar alias.
- **Sin restricción de hosts por `APP_ENV`**: se acepta cualquier URL `http`/`https` y el host efectivo queda en el log de arranque.
- **URLs normalizadas**: `HttpUrl` agrega `/` al final (`https://api.remarkets.primary.com.ar/`). El código que construya los clientes debe pasar `str(url).rstrip("/")`.
- **Tests aislados del `.env` local**: los tests de `Settings` desactivan el `env_file` en proceso; solo los de URL inválida y stderr sin secretos corren además `python -m app` en un subproceso, con valores que pisan cualquier `.env`.

## Pendiente

- Construir los clientes de `matriz-client` y `market-data-client`, inyectarlos como dependencias de FastAPI y usarlos en servicios.
