# Requirements: variables de configuración de `market-data-client` y `matriz-client` en el `.env`

## Introduction

El backend depende de dos librerías internas (`backend/pyproject.toml`): `market-data-client` (v0.7.1) y `matriz-client` (v0.4.0). Ambas leen su configuración de variables de entorno, pero hoy ninguna de esas variables figura en `.env.example` ni en `Settings` (`backend/app/core/config.py`). Quien levanta el proyecto no tiene forma de saber qué variables hacen falta, y el backend no puede validarlas al arrancar.

Variables que leen las librerías (relevadas del código instalado):

| Librería | Variable | Requerida por la librería | Default de la librería |
|---|---|---|---|
| `matriz-client` | `PRIMARY_USER` | sí | — |
| `matriz-client` | `PRIMARY_PASSWORD` | sí (secreto) | — |
| `matriz-client` | `PRIMARY_BASE_URL` | no | `https://api.remarkets.primary.com.ar` (sandbox reMarkets) |
| `market-data-client` | `MARKET_DATA_CLIENT_ID` | sí | — |
| `market-data-client` | `MARKET_DATA_CLIENT_SECRET` | sí (secreto) | — |
| `market-data-client` | `MARKET_DATA_AUDIENCE` | sí | — |
| `market-data-client` | `MARKET_DATA_AUTH0_TOKEN_URL` | sí (URL absoluta) | — |
| `market-data-client` | `MARKET_DATA_BASE_URL` | no | `https://market-data-develop.bbsa.com.ar/api` |

Esta feature expone esas ocho variables en el único `.env` de la raíz: las documenta en `.env.example`, las agrega tipadas a `Settings` y garantiza que los secretos no aparezcan en logs. No construye todavía ningún cliente ni agrega endpoints: no hay lógica de negocio que los use.

## User Stories

- US-1: As a desarrollador que levanta el proyecto, I want que `.env.example` liste y explique todas las variables que necesitan `market-data-client` y `matriz-client`, so that pueda completar mi `.env` sin leer el código de las librerías.
- US-2: As a desarrollador del backend, I want que esas variables estén tipadas y validadas en `Settings`, so that el código futuro que construya los clientes lea la configuración desde un único lugar y un valor mal formado se detecte al arrancar.
- US-3: As a operador de estrategias, I want que las credenciales de Matriz y de market data nunca aparezcan en logs ni en representaciones de objetos, so that no se filtren secretos al compartir logs o trazas.
- US-4: As a desarrollador que usa Docker Compose, I want que el contenedor del backend reciba esas variables desde el mismo `.env` de la raíz, so that el backend se comporte igual dentro y fuera de Docker.

## Acceptance Criteria (EARS notation)

- AC-1: WHEN se abre `.env.example` THEN the system SHALL contener una sección para `matriz-client` con `PRIMARY_USER`, `PRIMARY_PASSWORD` y `PRIMARY_BASE_URL`, y una sección para `market-data-client` con `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE`, `MARKET_DATA_AUTH0_TOKEN_URL` y `MARKET_DATA_BASE_URL`. (US-1)
- AC-2: WHEN se abre `.env.example` THEN the system SHALL mostrar, antes de cada una de esas ocho variables, un comentario en español que indique para qué sirve, si la librería la exige y, si tiene default, cuál es. (US-1)
- AC-3: WHEN se abre `.env.example` THEN the system SHALL usar para `PRIMARY_PASSWORD` y `MARKET_DATA_CLIENT_SECRET` un valor de ejemplo no secreto (por ejemplo `change-me-local-only`), de modo que gitleaks no reporte hallazgos sobre el archivo. (US-1, US-3)
- AC-4: WHEN se abre `.env.example` THEN the system SHALL tener como valor de ejemplo de `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` los mismos defaults de cada librería (`https://api.remarkets.primary.com.ar` y `https://market-data-develop.bbsa.com.ar/api`), de modo que el ejemplo apunte a entornos de prueba y no a producción. (US-1)
- AC-5: WHEN el backend carga `Settings` con las ocho variables definidas en el entorno o en el `.env` de la raíz THEN the system SHALL exponer cada una como un campo tipado de `Settings` cuyo valor coincide con el definido. (US-2)
- AC-6: WHEN el backend carga `Settings` sin `PRIMARY_BASE_URL` o sin `MARKET_DATA_BASE_URL` THEN the system SHALL usar el default de la librería correspondiente (`https://api.remarkets.primary.com.ar` y `https://market-data-develop.bbsa.com.ar/api`). (US-2)
- AC-7: IF `PRIMARY_BASE_URL`, `MARKET_DATA_BASE_URL` o `MARKET_DATA_AUTH0_TOKEN_URL` tiene un valor que no es una URL absoluta `http` o `https` THEN the system SHALL abortar el arranque con exit code `1` y un mensaje en stderr que nombre la variable inválida, igual que hoy `load_settings()` hace con `DATABASE_URL`. (US-2)
- AC-8: IF el backend arranca sin alguna de las variables que la librería exige (`PRIMARY_USER`, `PRIMARY_PASSWORD`, `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE`, `MARKET_DATA_AUTH0_TOKEN_URL`) THEN the system SHALL arrancar igual y `GET /api/health` SHALL responder `200`, porque ningún código del backend construye todavía los clientes (ver Open Question 1). (US-2)
- AC-9: WHEN se obtiene el `repr()` o `str()` de `Settings`, o se loguea su contenido con structlog THEN the system SHALL mostrar `PRIMARY_PASSWORD` y `MARKET_DATA_CLIENT_SECRET` enmascarados (sin el valor real en la salida). (US-3)
- AC-10: IF `load_settings()` aborta por una variable inválida THEN the system SHALL omitir de stderr el valor de `PRIMARY_PASSWORD` y de `MARKET_DATA_CLIENT_SECRET`. (US-3)
- AC-11: WHEN se levanta el backend con `docker-compose.dev.yml` o `docker-compose.prod.yml` y las ocho variables están en el `.env` de la raíz THEN the system SHALL entregar al contenedor del backend las ocho variables con los mismos valores, sin redefinirlas en el bloque `environment:` del servicio. (US-4)
- AC-12: WHEN corre `scripts/gate.sh backend full` sin un `.env` con estas variables (como en CI) THEN the system SHALL salir con `0`. (US-2)

## Out of Scope

- Construir instancias de `matriz_client` o `market_data_client` (sync o async), inyectarlas como dependencias de FastAPI o usarlas en servicios.
- Endpoints nuevos, cambios en `backend/openapi.json` o en el cliente Orval del frontend.
- Exponer estas variables al frontend: no llevan prefijo `VITE_` y no llegan al bundle.
- Parámetros de la librería que no se leen del entorno (`max_retries`, `mutating_allowed`, `expected_host`, `strict_decode`, `token`, `token_expires_at`).
- Cambiar el secret de CI `MARKET_LIBS_TOKEN`, que sirve para instalar las librerías y no para configurarlas.
- Gestores de secretos externos (Vault, AWS Secrets Manager, etc.).

## Non-Functional Requirements

- Seguridad: ningún valor real de `PRIMARY_PASSWORD` ni de `MARKET_DATA_CLIENT_SECRET` se commitea — lo verifica gitleaks (lefthook y job `security`).
- Un único `.env` en la raíz: no se crean `backend/.env` ni `frontend/.env` — lo verifica `.claude/hooks/guard-paths.sh`.
- Los nombres de las variables son exactamente los que leen las librerías (los de la tabla de la Introduction), para que la librería y `Settings` lean el mismo valor sin traducciones.
- Cobertura: los tests nuevos de `Settings` mantienen la cobertura del backend en 85 % o más y no dependen del `.env` local del desarrollador.
- Definición de terminado: `scripts/gate.sh changed full` sale con `0`.

## Open Questions
- [x] ¿Las credenciales (`PRIMARY_USER`, `PRIMARY_PASSWORD`, `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE`, `MARKET_DATA_AUTH0_TOKEN_URL`) deben ser obligatorias al arrancar el backend? — **Resolved:** Obligatorias, con abortar el arranque si faltan — el error aparece antes, pero CI, los tests y `docker-compose` necesitan valores falsos.
  - Obligatorias, con abortar el arranque si faltan — el error aparece antes, pero CI, los tests y `docker-compose` necesitan valores falsos.
  - Obligatorias solo con `APP_ENV=production` — protege producción sin afectar el desarrollo, pero suma una regla condicional para testear.
- [x] Si se definen solo algunas variables de una librería (por ejemplo `PRIMARY_USER` sin `PRIMARY_PASSWORD`), ¿qué tiene que pasar? — **Resolved:** Validar «todo o nada» por librería y abortar si el grupo está incompleto — detecta enseguida un `.env` a medio completar, a cambio de una validación extra.
  - Validar «todo o nada» por librería y abortar si el grupo está incompleto — detecta enseguida un `.env` a medio completar, a cambio de una validación extra.
  - Aceptar cualquier combinación — es más simple, pero el error se ve recién al usar el cliente.
- [x] ¿Qué forma deben tener estas variables dentro de `Settings`? — **Resolved:** Recomiendo campos planos en `Settings`, nombrados en minúscula igual que cada variable: `primary_user: str`, `primary_password: SecretStr`, `primary_base_url: HttpUrl`, `market_data_client_id: str`, `market_data_client_secret: SecretStr`, `market_data_audience: str`, `market_data_auth0_token_url: HttpUrl` y `market_data_base_url: HttpUrl`. Así pydantic-settings los mapea a los nombres exactos que leen las librerías, sin `env_prefix` ni `env_nested_delimiter`. No conviene usar submodelos anidados (`settings.matriz.user`), porque obligarían a cambiar los nombres de las variables o a sumar alias. `SecretStr` enmascara los secretos en `repr()`, en `str()` y en los logs de structlog (AC-9, AC-10), y `HttpUrl` rechaza las URLs que no son `http`/`https` absolutas (AC-7). Según lo resuelto en las Open Questions 1 y 2, las seis credenciales no tienen default, el chequeo «todo o nada» por librería va en un `@model_validator(mode="after")`, y solo `primary_base_url` y `market_data_base_url` llevan como default el de cada librería. Con esa decisión hay que reescribir AC-8 y AC-12, y los tests y CI tienen que definir valores falsos de las credenciales.
- [x] ¿Hay que restringir los hosts de `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` según `APP_ENV`? — **Resolved:** Recomiendo aceptar cualquier URL `http`/`https` y registrar en el log, al arrancar, el host efectivo, sin incluir secretos. Así queda a la vista contra qué entorno (reMarkets o producción) opera el backend, lo que va con los objetivos de seguridad operativa y trazabilidad del proyecto. No bloquea el desarrollo y cuesta solo una línea de log estructurado.
  - Aceptar cualquier URL `http`/`https` y loguear al arrancar el host efectivo (sin secretos) — no bloquea nada, pero deja visible contra qué entorno se opera.
  - No validar hosts ni loguearlos — no agrega trabajo, pero no protege contra apuntar a producción por error.
- [x] ¿Cómo hay que tratar un valor vacío (`PRIMARY_USER=`) en el `.env`? — **Resolved:** Como error de arranque — es lo más estricto, pero choca con que las credenciales sean opcionales.
  - Como ausente (`None`) — se comporta igual que no definir la variable y evita credenciales vacías «válidas».
  - Como string vacío válido — no hace falta código extra, pero un `.env` copiado a medias pasa la validación.
  - Como error de arranque — es lo más estricto, pero choca con que las credenciales sean opcionales.

1. **¿Las credenciales son obligatorias al arrancar?** Hoy ningún código usa los clientes. El borrador (AC-8) las deja opcionales en `Settings` para que el backend, los tests y CI arranquen sin credenciales reales. La alternativa es exigirlas y abortar el arranque si faltan, lo que obliga a definir valores falsos en CI y en los tests. ¿Cuál preferís?
2. **¿Las URLs de producción deben poder bloquearse?** El borrador acepta cualquier URL `http`/`https` en `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL`. ¿Querés que, con `APP_ENV=development`, se rechacen hosts de producción (por ejemplo, que `PRIMARY_BASE_URL` solo acepte reMarkets) como control de seguridad operativa?

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Las credenciales (`PRIMARY_USER`, `PRIMARY_PASSWORD`, `MARKET_DATA_CLIENT_ID`, `MARKET_DATA_CLIENT_SECRET`, `MARKET_DATA_AUDIENCE`, `MARKET_DATA_AUTH0_TOKEN_URL`) deben ser obligatorias al arrancar el backend?** — Obligatorias, con abortar el arranque si faltan — el error aparece antes, pero CI, los tests y `docker-compose` necesitan valores falsos.
- **Si se definen solo algunas variables de una librería (por ejemplo `PRIMARY_USER` sin `PRIMARY_PASSWORD`), ¿qué tiene que pasar?** — Validar «todo o nada» por librería y abortar si el grupo está incompleto — detecta enseguida un `.env` a medio completar, a cambio de una validación extra.
- **¿Qué forma deben tener estas variables dentro de `Settings`?** — Recomiendo campos planos en `Settings`, nombrados en minúscula igual que cada variable: `primary_user: str`, `primary_password: SecretStr`, `primary_base_url: HttpUrl`, `market_data_client_id: str`, `market_data_client_secret: SecretStr`, `market_data_audience: str`, `market_data_auth0_token_url: HttpUrl` y `market_data_base_url: HttpUrl`. Así pydantic-settings los mapea a los nombres exactos que leen las librerías, sin `env_prefix` ni `env_nested_delimiter`. No conviene usar submodelos anidados (`settings.matriz.user`), porque obligarían a cambiar los nombres de las variables o a sumar alias. `SecretStr` enmascara los secretos en `repr()`, en `str()` y en los logs de structlog (AC-9, AC-10), y `HttpUrl` rechaza las URLs que no son `http`/`https` absolutas (AC-7). Según lo resuelto en las Open Questions 1 y 2, las seis credenciales no tienen default, el chequeo «todo o nada» por librería va en un `@model_validator(mode="after")`, y solo `primary_base_url` y `market_data_base_url` llevan como default el de cada librería. Con esa decisión hay que reescribir AC-8 y AC-12, y los tests y CI tienen que definir valores falsos de las credenciales.
- **¿Hay que restringir los hosts de `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` según `APP_ENV`?** — Recomiendo aceptar cualquier URL `http`/`https` y registrar en el log, al arrancar, el host efectivo, sin incluir secretos. Así queda a la vista contra qué entorno (reMarkets o producción) opera el backend, lo que va con los objetivos de seguridad operativa y trazabilidad del proyecto. No bloquea el desarrollo y cuesta solo una línea de log estructurado.
- **¿Cómo hay que tratar un valor vacío (`PRIMARY_USER=`) en el `.env`?** — Como error de arranque — es lo más estricto, pero choca con que las credenciales sean opcionales.
