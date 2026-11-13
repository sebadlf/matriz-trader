# Bugfix: `docker compose up --build` falla con "container matriz-trader-backend-1 is unhealthy"

## Resumen

Al levantar el stack de producción, el contenedor `backend` arranca uvicorn pero `GET /health` responde siempre **503** (`{"status":"degraded","database":"unavailable"}`). El healthcheck de compose falla 10 veces, `backend` queda `unhealthy`, `frontend` (que depende de `backend: service_healthy`) no arranca y compose aborta con `dependency failed to start`.

### Evidencia recogida (2026-11-12)

- `docker compose logs backend`: `Application startup complete.` seguido de `GET /health HTTP/1.1" 503 Service Unavailable` en cada sondeo.
- `docker inspect … .State.Health`: `unhealthy`, `FailingStreak: 15`, `HTTPError: HTTP Error 503`.
- `docker compose logs postgres`: en cada sondeo, `FATAL: password authentication failed for user "matriz"` (regla `host all all all scram-sha-256` de `pg_hba.conf`).
- `docker compose config`: `DATABASE_URL` del servicio `backend`/`worker` resuelve a `postgresql+psycopg://matriz:<password>@postgres:5432/matriz_trader`. Host, puerto, usuario y base coinciden con lo esperado; el error de Postgres es de autenticación (no de host/rol/base inexistente).
- El volumen `matriz-trader_pgdata` fue creado el **2026-10-30**; el `.env` fue modificado el **2026-11-12** (se desconoce qué líneas cambiaron). La imagen `postgres` aplica `POSTGRES_USER`/`POSTGRES_PASSWORD` **solo al inicializar un volumen vacío**; en volúmenes existentes los ignora (comportamiento documentado de la imagen).
- La contraseña actual del `.env` contiene un carácter `!`. Es válido sin percent-encoding en la parte userinfo de una URL (RFC 3986, sub-delims), así que **se infiere** que no es la causa; no se verificó aislándolo.
- Código (observado): `backend/src/backend/health.py::ping_database` captura `SQLAlchemyError` y devuelve `False` sin loguear nada; por eso el backend no deja rastro del error de autenticación.
- Código (observado): el `worker` no crea engine ni usa `DATABASE_URL` hoy, por lo que no se ve afectado por este fallo (solo depende de `postgres: service_healthy`).

### Causa raíz (hipótesis principal, a confirmar en diseño)

> Diagnóstico, no observación: la evidencia es consistente con esta hipótesis pero no la prueba. Ver Open Questions (prueba de confirmación).

La contraseña del rol `matriz` guardada en el volumen `pgdata` (fijada al inicializarlo el 2026-10-30) no coincide con el `POSTGRES_PASSWORD` actual del `.env`. El backend se autentica con la contraseña nueva y Postgres la rechaza. El healthcheck de `postgres` (`pg_isready`) no valida credenciales, por eso `postgres` aparece `healthy` y el problema recién se manifiesta en `backend`.

## Reproducción

Reproducción determinista desde cero (⚠️ el paso 1 borra el volumen; usar una copia del repo o un `COMPOSE_PROJECT_NAME` distinto, p. ej. `COMPOSE_PROJECT_NAME=matriz-repro`, para no perder los datos reales):

1. `docker compose down -v` para partir sin volumen `pgdata`.
2. En el `.env` de la raíz fijar `POSTGRES_PASSWORD=passA` (y `DATABASE_URL` coherente) y ejecutar `docker compose up -d postgres`; esperar a que esté `healthy` (esto inicializa el volumen con `passA`).
3. `docker compose down` (**sin** `-v`, conserva el volumen).
4. Cambiar en el `.env` `POSTGRES_PASSWORD=passB`.
5. Ejecutar `docker compose up --build` desde la raíz.
6. Esperar ~60 s (`start_period` 10 s + 10 reintentos cada 5 s del healthcheck de `backend`).
7. Observar la salida de compose y `docker compose logs backend postgres`.

Resultado esperado de la reproducción: compose termina con `dependency failed to start: container …-backend-1 is unhealthy` y `postgres` loguea `password authentication failed for user "matriz"`. Control negativo: repetir con `passA` en el paso 4 → el stack debe arrancar sano.

## Current Behavior

- WHEN el volumen `pgdata` fue inicializado con una contraseña distinta a la del `.env` actual THEN Postgres rechaza cada conexión del backend con `password authentication failed for user "matriz"`.
- WHEN ocurre ese rechazo THEN el healthcheck de `postgres` (`pg_isready`) sigue reportando `healthy`, porque no valida credenciales.
- WHEN el healthcheck de `backend` llama a `GET /health` y la autenticación falla THEN responde 503 `{"status":"degraded","database":"unavailable"}` en cada sondeo (no se recupera solo mientras no cambien las credenciales).
- WHEN el healthcheck de `backend` agota sus reintentos THEN compose marca `backend` como `unhealthy`, no arranca `frontend` y termina con `dependency failed to start: container matriz-trader-backend-1 is unhealthy`.
- WHEN ocurre este fallo THEN el único indicio de la causa real está en los logs de `postgres`; ni la salida de `docker compose up` ni los logs de `backend` mencionan un error de autenticación (`ping_database` descarta la excepción sin loguearla).

## Expected Behavior

- WHEN se ejecuta `docker compose up --build` con un `.env` cuyas credenciales coinciden con las del volumen `pgdata` THEN el backend SHALL conectarse a Postgres, `GET /health` SHALL responder 200 `{"status":"ok","database":"ok"}` y `frontend` SHALL arrancar en `http://localhost:${FRONTEND_PORT:-8080}`.
- WHEN `ping_database` falla por un `SQLAlchemyError` (incluido un error de autenticación) THEN el backend SHALL loguear la causa (tipo de excepción y mensaje del driver, p. ej. `password authentication failed for user "matriz"`) en sus propios logs, no solo en los de `postgres`.
- WHEN el backend loguea ese error THEN el log SHALL NOT incluir la contraseña ni el `DATABASE_URL` completo.
- WHEN el desarrollador cambia `POSTGRES_PASSWORD` en el `.env` THEN la documentación (`CLAUDE.md` raíz y/o `.env.example`) SHALL indicar que el cambio no se aplica a un volumen ya inicializado y cómo realinear credenciales: `ALTER ROLE matriz WITH PASSWORD '…'` (preserva datos) o recrear el volumen con `docker compose down -v` (con advertencia explícita de pérdida de datos).
- WHEN se realinean las credenciales en el entorno local afectado THEN `docker compose up --build` SHALL dejar `backend` y `frontend` `healthy` y `GET /health` SHALL responder 200.

## Unchanged Behavior

- WHEN `GET /health` se invoca con la base accesible THEN SHALL CONTINUE TO responder 200 `{"status":"ok","database":"ok"}`, y 503 `{"status":"degraded","database":"unavailable"}` cuando no lo es (contrato de `frontend/openapi.json`, `operation_id="getHealth"`, sin cambios). El cuerpo de la respuesta SHALL CONTINUE TO no exponer detalles del error (el diagnóstico va a logs, no a la API).
- WHEN Postgres está caído al arrancar el backend THEN el backend SHALL CONTINUE TO arrancar igual (el engine no conecta al crearse) y reportar 503 hasta que la base esté disponible, recuperándose sin reinicio.
- WHEN se levanta el stack sobre un volumen `pgdata` vacío (`docker compose down -v && docker compose up --build`) THEN SHALL CONTINUE TO inicializar el rol con las credenciales del `.env` y arrancar sano.
- WHEN se ejecuta `docker compose up postgres` para desarrollo THEN SHALL CONTINUE TO levantar solo la base en `${POSTGRES_PORT:-5432}`.
- WHEN se corre el backend local (`uv run uvicorn backend.main:app --reload --port 8000`) THEN SHALL CONTINUE TO usar el `DATABASE_URL` del `.env` (host `localhost`), mientras que en compose SHALL CONTINUE TO sobrescribirse con host `postgres`.
- WHEN el `worker` arranca en compose THEN SHALL CONTINUE TO depender solo de `postgres: service_healthy` y recibir el mismo `DATABASE_URL` que el backend.
- WHEN falta una variable obligatoria THEN `load_settings()` SHALL CONTINUE TO salir con código 2 y `Missing required environment variables: ...`.
- WHEN existen datos en el volumen `pgdata` THEN la solución SHALL CONTINUE TO preservarlos salvo que el usuario elija explícitamente recrear el volumen.
- WHEN se ejecuta `scripts/check.sh` THEN SHALL CONTINUE TO pasar (ruff, pyright strict, tests de backend incluido `test_openapi_snapshot.py`).
- WHEN el stack está sano THEN `uv run pytest e2e` SHALL CONTINUE TO pasar.
- Se SHALL CONTINUE TO usar un único `.env` en la raíz, sin commitear secretos (`.env.example` solo con valores de ejemplo).

## Environment

- Host: macOS (Darwin 25.3.0), Docker Desktop (`docker:desktop-linux`), Docker Engine 25.0.3, Docker Compose v2.24.5-desktop.1.
- Comando: `docker compose up --build` desde la raíz del repo (`main`, último commit `fd1864a`).
- Imágenes: `postgres:17-alpine`, `python:3.13-slim` + `ghcr.io/astral-sh/uv:0.9.0` (backend/worker), `node:24-alpine` → `nginx:1.27-alpine` (frontend).
- Volumen: `matriz-trader_pgdata`, creado 2026-10-30T23:04:12Z.
- Config relevante: `docker-compose.yml` (healthchecks de `postgres` con `pg_isready` y de `backend` con `urllib` a `/health`), `backend/src/backend/health.py`, `.env` (`POSTGRES_USER=matriz`, `POSTGRES_DB=matriz_trader`, `POSTGRES_PORT=5432`).

## Open Questions
- [x] ¿Qué alcance debe tener el fix? — **Resolved:** Elijo esta opción: **logs de diagnóstico en `backend` + documentación + realineación manual del entorno local**. Es un cambio mínimo y no toca la orquestación. Así se corrige la falta de diagnóstico en `ping_database` y el problema de documentación que causó la falla, sin cambiar el healthcheck de `postgres` ni arriesgar lo que hoy funciona en compose.
  - Logs de diagnóstico en `backend` + documentación + realineación manual del entorno local — cambio mínimo y sin tocar la orquestación.
- [x] ¿Cómo se realinean las credenciales del volumen `matriz-trader_pgdata` afectado? — **Resolved:** Ejecutar `ALTER ROLE matriz WITH PASSWORD '…'` mediante `docker compose exec postgres psql` (por socket local), lo que conserva todos los datos. Es la única opción que cumple el requisito de preservar los datos de `pgdata` sin depender de recordar la contraseña original, y además sirve como prueba de confirmación de la hipótesis.
  - `ALTER ROLE matriz WITH PASSWORD '…'` vía `docker compose exec postgres psql` (socket local) — conserva todos los datos.
  - Recrear el volumen con `docker compose down -v` — más simple y deja un estado limpio, pero se pierden los datos actuales.
  - Volver a poner en el `.env` la contraseña original con la que se inicializó el volumen — no toca la base, pero solo sirve si esa contraseña se conoce.
- [x] ¿Autorizás ejecutar ahora la prueba de confirmación (`ALTER ROLE` por socket + reiniciar `backend`) antes de diseñar? — **Resolved:** **Sí, ejecutarla ahora**: confirma la hipótesis sin perder datos y además deja el entorno arreglado.

Ya se eligió `ALTER ROLE` como forma de realinear las credenciales, así que esta prueba no agrega riesgo ni trabajo extra. A cambio, evita diseñar el fix sobre una causa que todavía no está confirmada.
  - Sí, ejecutarla ahora — confirma la hipótesis sin pérdida de datos y de paso deja el entorno arreglado.
  - No ejecutarla y diseñar sobre la hipótesis — es más rápido, pero existe el riesgo de corregir la causa equivocada.
- [x] ¿Con qué frecuencia debe loguear `ping_database` los fallos de conexión? — **Resolved:** **Recomendación:** loguear solo cuando cambia el estado: `ERROR` al pasar de ok a unavailable (con el tipo de excepción y el mensaje del driver, sin la contraseña ni el `DATABASE_URL` completo) e `INFO` al volver de unavailable a ok.

**Por qué:** con un único `ERROR` ya queda la causa en los logs del backend sin escribir una línea cada 5 s, y el `INFO` marca cuándo se recuperó. Para eso basta guardar el último estado en el proceso. La opción de `ERROR` y después `DEBUG` también necesita guardar ese estado, pero no registra la recuperación.
  - Solo al cambiar de estado (ok→unavailable con `ERROR`, unavailable→ok con `INFO`) — logs limpios, pero hace falta guardar el estado en el proceso.
  - Un `WARNING` por cada sondeo fallido — implementación trivial, pero genera un log cada 5 s mientras dure el fallo.
  - El primer fallo con `ERROR` y los siguientes con `DEBUG` — logs poco ruidosos sin perder detalle si se sube el nivel.
- [x] ¿Dónde se documenta la advertencia sobre cambiar `POSTGRES_PASSWORD` con un volumen ya inicializado? — **Resolved:** **Comentario en `.env.example` junto a `POSTGRES_PASSWORD` + sección corta en el `CLAUDE.md` raíz.** El aviso aparece justo donde se edita la variable, y el `CLAUDE.md`, que ya es la referencia del repo y la que cita el Expected Behavior, explica cómo realinear la contraseña con `ALTER ROLE` o con `down -v`, sin crear un documento nuevo.
  - Comentario en `.env.example` junto a `POSTGRES_PASSWORD` + sección corta en el `CLAUDE.md` raíz — visible justo al editar la variable.
  - Solo en el `CLAUDE.md` raíz — un único lugar, pero menos visible para quien edita el `.env`.
  - Una sección de troubleshooting en un `README.md` nuevo — más completa, pero agrega un documento que hoy no existe.

1. **Alcance del fix** (decisión del usuario): ¿basta con diagnóstico visible en logs de `backend` + documentación + realineación manual del entorno local, o se quiere además una corrección automática (p. ej. que el healthcheck de `postgres` valide credenciales por TCP con `PGPASSWORD` para fallar antes y con mensaje claro)?
2. **Realineación del entorno afectado**: ¿los datos actuales de `matriz-trader_pgdata` deben preservarse (→ `ALTER ROLE`) o se puede recrear el volumen (`docker compose down -v`)?
3. **Confirmación de la hipótesis**: antes de diseñar, ejecutar una prueba decisiva sin perder datos — `docker compose exec postgres psql -U matriz -d matriz_trader -c "ALTER ROLE matriz WITH PASSWORD '<POSTGRES_PASSWORD del .env>'"` (por socket local, `trust`) y relanzar `backend`; si `/health` pasa a 200, la hipótesis queda confirmada. ¿Autorizás ejecutarla?
4. **Volumen de logs**: el healthcheck sondea cada 5 s; ¿se acepta un log de error por sondeo fallido o se prefiere limitarlo (p. ej. solo al cambiar de estado ok→unavailable)?

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Qué alcance debe tener el fix?** — Elijo esta opción: **logs de diagnóstico en `backend` + documentación + realineación manual del entorno local**. Es un cambio mínimo y no toca la orquestación. Así se corrige la falta de diagnóstico en `ping_database` y el problema de documentación que causó la falla, sin cambiar el healthcheck de `postgres` ni arriesgar lo que hoy funciona en compose.
- **¿Cómo se realinean las credenciales del volumen `matriz-trader_pgdata` afectado?** — Ejecutar `ALTER ROLE matriz WITH PASSWORD '…'` mediante `docker compose exec postgres psql` (por socket local), lo que conserva todos los datos. Es la única opción que cumple el requisito de preservar los datos de `pgdata` sin depender de recordar la contraseña original, y además sirve como prueba de confirmación de la hipótesis.
- **¿Autorizás ejecutar ahora la prueba de confirmación (`ALTER ROLE` por socket + reiniciar `backend`) antes de diseñar?** — **Sí, ejecutarla ahora**: confirma la hipótesis sin perder datos y además deja el entorno arreglado.
- **¿Con qué frecuencia debe loguear `ping_database` los fallos de conexión?** — **Recomendación:** loguear solo cuando cambia el estado: `ERROR` al pasar de ok a unavailable (con el tipo de excepción y el mensaje del driver, sin la contraseña ni el `DATABASE_URL` completo) e `INFO` al volver de unavailable a ok.
- **¿Dónde se documenta la advertencia sobre cambiar `POSTGRES_PASSWORD` con un volumen ya inicializado?** — **Comentario en `.env.example` junto a `POSTGRES_PASSWORD` + sección corta en el `CLAUDE.md` raíz.** El aviso aparece justo donde se edita la variable, y el `CLAUDE.md`, que ya es la referencia del repo y la que cita el Expected Behavior, explica cómo realinear la contraseña con `ALTER ROLE` o con `down -v`, sin crear un documento nuevo.
