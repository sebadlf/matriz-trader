# Bugfix: `/orders` no permite ver, crear ni cancelar órdenes

> **Naturaleza del cambio.** Aunque se registra como bugfix, es funcionalidad faltante: la ruta
> `/orders` existe pero es un placeholder. Este documento fija el comportamiento actual verificado en
> el repo, el esperado y lo que no debe romperse. Las decisiones que el repo no resuelve quedan en
> [Preguntas abiertas](#preguntas-abiertas), cada una con una **propuesta por defecto** que se toma si
> nadie la objeta antes de la fase de diseño.

## Evidencia del repo (verificada)

| Hecho | Fuente |
|---|---|
| `OrdersPage` solo renderiza `<Typography.Title level={2} data-testid="page-ordenes">Órdenes</Typography.Title>` | `frontend/src/pages/OrdersPage.tsx` |
| Los tests del layout dependen de `page-ordenes` y del ítem «Órdenes» | `frontend/src/layout/AppLayout.test.tsx` |
| El backend solo registra `health.router` (`GET /health`) | `backend/src/backend/main.py` |
| CORS del backend permite **solo `GET`** (`allow_methods=["GET"]`) | `backend/src/backend/main.py` |
| `matriz-client==0.3.0` es dependencia solo de `matriz-worker`; `matriz-backend` no la declara | `worker/pyproject.toml`, `backend/pyproject.toml` |
| `MatrizClientGateway` solo expone `connect()` (`login()`) y `close()` | `worker/src/worker/matriz_gateway.py` |
| `model` no define tablas de órdenes ni de cuentas | `model/src/model/` |
| React Query global: `retry: 1`, `refetchOnWindowFocus: false`, sin `refetchInterval` | `frontend/src/queryClient.ts` |
| `new_order(symbol, side, qty: int, account, price: float \| None = None, *, order_type="LIMIT", time_in_force="DAY", market_id="ROFX", cancel_previous=False, iceberg=False, display_qty=None, expire_date=None)` | `matriz_client/client.py` |
| `new_order` y `cancel_order` devuelven `NewOrderResponse(clientId, proprietary)`, **no** el estado de la orden | `matriz_client/models.py` |
| `cancel_order(cl_ord_id, proprietary)`; `get_order_status(cl_ord_id, proprietary)`; `get_all_orders(account_id)`, `get_active_orders(account_id)`, `get_filled_orders(account_id)` | `matriz_client/client.py` |
| `Order`: `clOrdId`, `proprietary`, `accountId`, `instrumentId` (`symbol`, `marketId`), `price`, `orderQty`, `ordType`, `side`, `timeInForce`, `transactTime`, `cumQty`, `leavesQty`, `avgPx`, `status`, `text` (todos opcionales) | `matriz_client/models.py` |
| `OrderType = LIMIT \| MARKET \| STOP_LIMIT \| STOP_LIMIT_MERVAL`; `TimeInForce = DAY \| IOC \| FOK \| GTD`; `MarketId = "ROFX"` (único valor) | `matriz_client/types.py` |
| `OrderStatus` = `NEW`, `PENDING_NEW`, `PENDING_REPLACE`, `PENDING_CANCEL`, `REJECTED`, `PENDING_APPROVAL`, `CANCELLED`, `REPLACED`, `FILLED`, `PARTIALLY_FILLED` | `matriz_client/types.py` |
| No existe ningún método para listar cuentas | `matriz_client/client.py` |

## Reproduction

1. `cp .env.example .env` y completar credenciales; `uv sync`; `cd frontend && npm ci --include=dev`.
2. Levantar el stack (`docker compose up --build`) o, en dev, `docker compose up postgres`,
   `uv run uvicorn backend.main:app --reload --port 8000`, `uv run python -m worker` y
   `cd frontend && npm run dev`.
3. Abrir la app y hacer clic en el ítem de menú «Órdenes» (o navegar a `/orders`).
4. Observar que solo aparece el título «Órdenes»: no hay listado, ni botón de alta, ni acciones.
5. Consultar `frontend/openapi.json` (o `GET /openapi.json` del backend): el único path es `/health`.

## Current Behavior

- **CB-1** WHEN el usuario navega a `/orders` THEN la página muestra únicamente el título «Órdenes» (`data-testid="page-ordenes"`), sin listado de órdenes ni estados de carga, vacío o error.
- **CB-2** WHEN el usuario busca cómo crear una orden en `/orders` THEN no existe botón ni modal de alta.
- **CB-3** WHEN el usuario quiere cancelar una orden THEN no existe acción «Cancelar» ni forma de hacerlo desde la UI.
- **CB-4** WHEN el frontend necesita órdenes, cuentas o instrumentos THEN el contrato `frontend/openapi.json` no expone ningún endpoint para ellos (solo `GET /health`).
- **CB-5** WHEN el sistema necesita operar órdenes con Matriz THEN ningún componente lo hace: `matriz_gateway.py` solo ejecuta `login()` y el backend no depende de `matriz-client`.
- **CB-6** WHEN se necesita la lista de cuentas THEN no existe caché de cuentas en ningún lado (ni tabla, ni configuración, ni endpoint) y `matriz-client` no ofrece cómo obtenerlas.
- **CB-7** WHEN el frontend de dev (origen distinto) hiciera un `POST`/`DELETE` al backend THEN el preflight CORS fallaría, porque el backend solo permite `GET`.

## Expected Behavior

### Listado

- **EB-1** WHEN el usuario entra a `/orders` THEN el sistema SHALL pedir el listado de órdenes y mostrar un indicador de carga hasta recibir la respuesta.
- **EB-2** WHEN el listado se recibe con órdenes THEN el sistema SHALL mostrar una tabla (Ant Design `Table`) con, como mínimo, las columnas: cuenta (`accountId`), símbolo (`instrumentId.symbol`), lado (`side`), tipo (`ordType`), cantidad (`orderQty`), precio (`price`), cantidad ejecutada (`cumQty`), cantidad remanente (`leavesQty`), estado (`status`) y hora (`transactTime`).
- **EB-3** WHEN un campo opcional de la orden viene vacío (p. ej. `price` en una orden `MARKET`) THEN la celda SHALL mostrar un marcador neutro (`—`) y no `null`, `undefined` ni `NaN`.
- **EB-4** WHEN el listado se recibe vacío THEN el sistema SHALL mostrar un estado vacío explícito («No hay órdenes») y el botón de alta SHALL seguir disponible.
- **EB-5** WHEN el pedido del listado falla THEN el sistema SHALL mostrar un mensaje de error con el detalle devuelto por la API y una acción para reintentar; el botón de alta SHALL seguir disponible.
- **EB-6** El sistema SHALL clasificar los estados de `OrderStatus` así (se adopta la clasificación del enunciado sin cambios):
  - **No finales:** `NEW`, `PENDING_NEW`, `PENDING_REPLACE`, `PENDING_CANCEL`, `PENDING_APPROVAL`, `PARTIALLY_FILLED`.
  - **Finales:** `REJECTED`, `CANCELLED`, `REPLACED`, `FILLED`.
  - Una orden con `status` nulo o con un valor fuera del enum SHALL tratarse como **no final** (para no detener el refresco por un dato incompleto) y mostrarse tal cual.
  - Esta clasificación SHALL vivir en un único lugar compartido por el refresco y por la regla de cancelabilidad.
- **EB-7** WHEN al menos una orden visible está en estado no final THEN el sistema SHALL volver a pedir el listado cada *N* segundos (ver PA-4).
- **EB-8** WHEN todas las órdenes visibles están en estado final (o el listado está vacío) THEN el sistema SHALL detener el refresco periódico.
- **EB-9** WHEN el refresco periódico está detenido y el usuario pulsa «Actualizar» THEN el sistema SHALL volver a pedir el listado; si aparece una orden no final, el refresco periódico SHALL reanudarse. «Actualizar» SHALL estar disponible siempre.
- **EB-10** WHEN un refresco periódico falla habiendo datos previos THEN el sistema SHALL conservar la última tabla visible y mostrar el error sin vaciarla.

### Cancelación

- **EB-11** WHEN una orden está en estado no final distinto de `PENDING_CANCEL` THEN su fila SHALL mostrar la acción «Cancelar» habilitada.
- **EB-12** WHEN una orden está en estado final o en `PENDING_CANCEL` THEN su fila SHALL NOT ofrecer «Cancelar» habilitada.
- **EB-13** WHEN el usuario pulsa «Cancelar» THEN el sistema SHALL pedir confirmación (Ant Design `Popconfirm` o `Modal.confirm`) antes de cualquier llamada.
- **EB-14** WHEN el usuario confirma THEN el sistema SHALL invocar `cancel_order(cl_ord_id, proprietary)` con el `clOrdId` y `proprietary` de esa fila, a través del endpoint del backend (ver PA-5), mostrando la acción en estado de carga y evitando dobles envíos.
- **EB-15** WHEN la cancelación es aceptada THEN la fila SHALL reflejar el nuevo estado sin recargar la página: el sistema SHALL volver a pedir el listado (o el estado de esa orden vía `get_order_status`) y, como `cancel_order` no devuelve estado, mientras la API no informe otro valor la fila SHALL mostrar `PENDING_CANCEL` y «Cancelar» SHALL quedar deshabilitado. El refresco periódico SHALL quedar activo mientras la orden siga no final.
- **EB-16** WHEN la cancelación falla THEN la fila SHALL NOT cambiar de estado y el sistema SHALL mostrar el error devuelto por la API.
- **EB-17** WHEN el usuario descarta la confirmación THEN el sistema SHALL NOT llamar a la API.

### Modal de alta

- **EB-18** WHEN el usuario pulsa «Nueva orden» en `/orders` THEN el sistema SHALL abrir un modal (Ant Design `Modal`) sin cambiar la ruta.
- **EB-19** WHEN el usuario pulsa «Cancelar» del modal, la cruz o Escape THEN el modal SHALL cerrarse sin emitir la orden.
- **EB-20** El campo **Cuenta** SHALL ser un `Select` buscable (`showSearch`) alimentado por el caché de cuentas (ver PA-1); SHALL NOT aceptar texto libre.
- **EB-21** WHEN el caché de cuentas está vacío THEN el selector SHALL mostrar un estado vacío que explique que no hay cuentas configuradas y cómo cargarlas, y el envío SHALL quedar bloqueado.
- **EB-22** El campo **Activo** SHALL ser un `Select` buscable por símbolo, alimentado por `get_all_instruments` (`instrumentId.symbol` + `instrumentId.marketId`) expuesto por el backend; SHALL NOT aceptar texto libre. La opción elegida SHALL enviar `symbol` y `market_id`.
- **EB-23** WHEN la lista de instrumentos está cargando o falla THEN el selector SHALL mostrar el estado de carga o el error correspondiente y el envío SHALL quedar bloqueado.
- **EB-24** El campo **Lado** SHALL ofrecer exactamente Compra (`BUY`) y Venta (`SELL`).
- **EB-25** El campo **Tipo** SHALL ofrecer exactamente Market (`MARKET`) y Limit (`LIMIT`). `STOP_LIMIT` y `STOP_LIMIT_MERVAL` SHALL NOT ofrecerse.
- **EB-26** WHEN el tipo es `LIMIT` THEN **Precio** SHALL estar visible, editable y ser obligatorio, numérico y mayor a cero.
- **EB-27** WHEN el tipo es `MARKET` THEN **Precio** SHALL estar oculto o deshabilitado y SHALL NOT enviarse en el pedido (ni en el body del backend ni a `new_order`, que recibe `price=None`).
- **EB-28** **Cantidad** SHALL ser obligatoria, entera y mayor a cero; valores decimales, cero, negativos o vacíos SHALL bloquear el envío. El backend SHALL validar lo mismo y responder `422` si no se cumple.
- **EB-29** Alcance de los demás argumentos de `new_order` (decisión de este requerimiento):

  | Argumento | Decisión | Valor enviado |
  |---|---|---|
  | `order_type` | Entra (Market / Limit) | `MARKET` \| `LIMIT` |
  | `time_in_force` | **Fuera** de la UI | default de la librería `DAY` |
  | `expire_date` | **Fuera** (solo aplica a `GTD`) | no se envía |
  | `iceberg` / `display_qty` | **Fuera** | `False` / no se envía |
  | `cancel_previous` | **Fuera** | `False` |
  | `market_id` | No editable: se toma del instrumento elegido | hoy siempre `ROFX` |

  Si se decide incluir `time_in_force`, ver PA-7.
- **EB-30** WHEN algún campo obligatorio es inválido THEN el botón de envío SHALL quedar deshabilitado o el formulario SHALL mostrar el error en el campo, y SHALL NOT llamarse a la API.
- **EB-31** WHEN se envía la orden THEN el botón de envío SHALL mostrar estado de carga y SHALL NOT permitir un segundo envío hasta recibir respuesta.
- **EB-32** WHEN la API responde con error THEN el modal SHALL permanecer abierto, conservar todos los valores cargados y mostrar el mensaje de error.
- **EB-33** WHEN la API responde con éxito THEN el modal SHALL cerrarse, el formulario SHALL reiniciarse para la próxima apertura y el listado SHALL volver a pedirse de modo que la orden nueva aparezca en él (si corresponde al filtro activo, ver PA-2/PA-3); como la orden nueva no es final, el refresco periódico SHALL reanudarse.

### Backend / contrato / integración

- **EB-34** El backend SHALL exponer los endpoints necesarios (listar órdenes, crear orden, cancelar orden, listar instrumentos, listar cuentas del caché) con modelos Pydantic de request/response tipados; `frontend/openapi.json` SHALL regenerarse con `uv run python -m backend.export_openapi` y el cliente con `npm run generate:api`.
- **EB-35** Los errores de Matriz (`MatrizClientError`, `httpx.HTTPError`) SHALL traducirse a respuestas HTTP con cuerpo de error legible (p. ej. `502` para fallos de Matriz, `422` para validación), sin filtrar credenciales ni tokens.
- **EB-36** WHEN el frontend de dev llama a endpoints no-`GET` THEN la configuración CORS del backend SHALL permitir los métodos que esos endpoints usen (al menos `POST`; `DELETE` si la cancelación se modela así).
- **EB-37** El import de `matriz_client` SHALL seguir concentrado en un único módulo del repo (ver PA-5 para cuál).
- **EB-38** Toda configuración nueva (intervalo de refresco, cuentas, etc.) SHALL vivir en el `.env` raíz y documentarse en `.env.example`, con settings de `pydantic-settings` tipados.
- **EB-39** La integración con Matriz SHALL testearse con un fake del gateway (sin red ni credenciales); la UI SHALL testearse con Vitest y router en memoria, cubriendo carga, vacío, error, refresco condicional, cancelación (éxito, error, descartada) y modal (validación, Market vs Limit, error, éxito, Escape).

## Unchanged Behavior

- **UB-1** WHEN el usuario navega a `/orders` THEN la página SHALL CONTINUE TO renderizar el título «Órdenes» con `data-testid="page-ordenes"`.
- **UB-2** WHEN se renderiza la app THEN el layout (`AppLayout`) y el ítem de menú «Órdenes» SHALL CONTINUE TO comportarse igual, y `AppLayout.test.tsx` SHALL CONTINUE TO pasar sin cambios.
- **UB-3** WHEN se navega a las demás rutas (Health, Estrategias) THEN SHALL CONTINUE TO renderizar lo mismo que hoy.
- **UB-4** WHEN se llama a `GET /health` THEN SHALL CONTINUE TO responder igual (incluido `503` si la base no está disponible).
- **UB-5** WHEN el frontend se comunica con el backend THEN SHALL CONTINUE TO hacerlo únicamente por el cliente Orval generado desde `frontend/openapi.json`; el frontend SHALL CONTINUE TO no llamar a Matriz directamente.
- **UB-6** WHEN se obtiene market data THEN SHALL CONTINUE TO hacerse solo con `market-data-client` a través de `worker/src/worker/market_data_gateway.py`; `matriz-client` SHALL CONTINUE TO no usarse para market data. `get_all_instruments` se considera metadata de instrumentos para el alta de órdenes, no market data (ver PA-8).
- **UB-7** WHEN arranca el worker THEN SHALL CONTINUE TO autenticarse con `login()` y salir con código 2 si faltan variables obligatorias.
- **UB-8** WHEN se corre `scripts/check.sh` THEN SHALL CONTINUE TO pasar: Ruff, Pyright strict (sin `# type: ignore` globales), Vitest y el resto de los gates.
- **UB-9** WHEN se configura el proyecto THEN SHALL CONTINUE TO existir un único `.env` en la raíz.
- **UB-10** WHEN se instalan dependencias del frontend THEN SHALL CONTINUE TO no haber dependencias npm nuevas (Ant Design + React Query alcanzan para tabla, modal, selects buscables, confirmación y polling).
- **UB-11** WHEN se configura React Query globalmente THEN `retry`, `retryDelay` y `refetchOnWindowFocus` de `queryClient.ts` SHALL CONTINUE TO tener los valores actuales; el polling se configura por query, no global.

## Environment

- **Repo:** monorepo `matriz-trader`, rama `main` (último commit `fec314e`).
- **Frontend:** Node 24, Vite, React 19, Ant Design 6, `@tanstack/react-query` 5, `react-router` 8, Orval 8, Vitest 5.
- **Backend / worker / model:** Python 3.13, workspace `uv`, FastAPI, SQLAlchemy 2 + Alembic, Pyright strict, Ruff.
- **Matriz:** `matriz-client==0.3.0` (solo en `matriz-worker`); por defecto sandbox reMarkets (`MATRIZ_BASE_URL=https://api.remarkets.primary.com.ar`).
- **Market data:** `market-data-client` (no interviene en esta pantalla).
- **Ejecución:** `docker compose up --build` (http://localhost:8080, nginx proxya `/api`) o dev local (frontend en `:5173`, backend en `:8000`, CORS por `CORS_ORIGINS`).

## Preguntas abiertas

Cada pregunta tiene una propuesta por defecto; el diseño la adopta salvo objeción.

- **PA-1 — Caché de cuentas: dónde vive y quién lo llena.** El repo no tiene ninguna fuente de cuentas.
  *Propuesta:* tabla `account` en `model` (migración Alembic) con `account_id` y alias opcional; se siembra desde una variable del `.env` raíz (`MATRIZ_ACCOUNTS`, lista separada por comas) al arrancar quien opere Matriz, y se expone con `GET /accounts`. Alternativa más simple: leer la variable directamente sin tabla. Si queda vacío aplica EB-21.
- **PA-2 — Alcance del listado: ¿una cuenta elegida o todas las del caché?** `get_all_orders`/`get_active_orders` piden `account_id`.
  *Propuesta:* todas las cuentas del caché (una llamada por cuenta, resultados unidos), con un filtro opcional por cuenta en la pantalla. Una falla en una cuenta no debe ocultar las demás: se muestran las obtenidas y se informa cuáles fallaron.
- **PA-3 — «Órdenes emitidas»: ¿históricas finales o solo activas? ¿Filtro?**
  *Propuesta:* `get_all_orders` (incluye finales del día según lo que devuelva Matriz), con un filtro «Solo activas / Todas» por defecto en «Todas». Con «Solo activas» la regla EB-8 aplica sobre lo visible.
- **PA-4 — Intervalo de refresco y si es configurable.**
  *Propuesta:* 5 s, configurable por variable del `.env` raíz expuesta al frontend como `VITE_ORDERS_REFRESH_MS` (build-time) — o fijo en código si se prefiere no agregar configuración.
- **PA-5 — ¿Crear/listar/cancelar pasan por el backend o por el worker?** Hoy solo el worker importa `matriz-client`, y solo para login. El frontend necesita respuestas síncronas (EB-32, EB-16).
  *Propuesta:* el backend pasa a depender de `matriz-client` y el **único módulo** que lo importa se mueve/crea en el backend (p. ej. `backend/src/backend/matriz_gateway.py`), lo que obliga a decidir qué pasa con el `login()` del worker (moverlo a un paquete compartido o que el worker deje de importarlo). Alternativa: el backend encola comandos en Postgres y el worker los ejecuta (asíncrono; complica errores inmediatos y el estado del modal). Requiere también que el backend reciba `MATRIZ_*` en `docker-compose.yml`.
- **PA-6 — ¿Confirmación también al emitir?**
  *Propuesta:* no; el modal ya es un paso explícito. Solo cancelar pide confirmación.
- **PA-7 — `time_in_force`.** Si se incluye: `DAY` (default), `IOC`, `FOK`; `GTD` exigiría `expire_date` y validación de fecha. *Propuesta:* fuera en esta iteración (EB-29).
- **PA-8 — `get_all_instruments` vs regla de market data.** Se asume que la lista de instrumentos de Matriz no es «market data» a los efectos de la regla de `CLAUDE.md`. Confirmar; si no, el selector de activos debería alimentarse de otra fuente.
- **PA-9 — Alternativa al polling:** streaming de execution reports por WebSocket (`matriz_client.ws_client`) empujado al frontend. Queda fuera de alcance; se deja como alternativa explícita a evaluar si el polling resulta insuficiente.
- **PA-10 — Credenciales y concurrencia del cliente en el backend.** Si el backend usa `matriz-client`, ¿una instancia compartida por proceso (login al arrancar, refresh de token de la librería) o por request? *Propuesta:* instancia por proceso inyectada como dependencia FastAPI, reemplazable por el fake en tests.

## Fuera de alcance

- Reemplazar órdenes (`replace_order`).
- Pantalla de Estrategias, market data en esta pantalla y libro de órdenes.
- Login, usuarios de la app y permisos por cuenta.
- Tipos `STOP_LIMIT` y `STOP_LIMIT_MERVAL`.
- Streaming por WebSocket de execution reports (solo como alternativa en PA-9).

## Open Questions
- [x] ¿Qué componente opera órdenes con Matriz y dónde queda el único módulo que importa `matriz_client`? — **Resolved:** El backend opera las órdenes de forma síncrona: listar, crear y cancelar pasan por endpoints FastAPI. Se descarta la cola en Postgres con el worker porque no da los errores inmediatos que piden EB-16 y EB-32. El único módulo que importa `matriz_client` pasa a un nuevo paquete del workspace `uv`, `matriz-broker` (`import broker`, layout `src/`, con `py.typed`), en `broker/src/broker/matriz_gateway.py`. Ese módulo absorbe el actual `worker/src/worker/matriz_gateway.py` y suma `list_orders`, `new_order`, `cancel_order` y `list_instruments` con tipos propios del repo. `matriz-backend` y `matriz-worker` dependen de `matriz-broker`, y `matriz-client==0.3.0` se declara solo en ese paquete. Así el worker conserva su `login()` (UB-7) sin que el worker dependa del backend ni el backend del worker. Además, `docker-compose.yml` pasa las variables `MATRIZ_*` al servicio `backend`, y `CLAUDE.md` se actualiza para indicar este módulo como único punto de acceso a Matriz.
- [x] Si el backend usa `matriz-client`, ¿cómo maneja la sesión con Matriz? — **Resolved:** **Login al primer uso, en diferido, con la instancia guardada en caché.** Así el backend arranca y `GET /health` sigue respondiendo (UB-4) aunque Matriz esté caído, y se evita un login por request que podría chocar contra el rate limit. Además coincide con la propuesta de PA-10: una instancia por proceso, inyectada como dependencia de FastAPI y reemplazable por el fake en los tests.
  - Login al primer uso, en diferido, con la instancia guardada en caché — el backend arranca aunque Matriz esté caído; el primer request tarda más.
  - Una instancia y un login por request — no hay estado compartido, pero se hace un login por cada llamada y se puede pegar contra el rate limit de Matriz.
- [x] ¿Dónde vive el caché de cuentas y cómo se llena? — **Resolved:** Recomiendo quedarse con la variable `MATRIZ_ACCOUNTS`: los settings la leen y `GET /accounts` la expone. Es lo más simple. No se puede editar sin reiniciar y no admite alias. Es la única opción planteada y alcanza para EB-20 y EB-21 sin sumar una tabla, una migración Alembic ni un proceso que siembre datos, porque `matriz-client` no ofrece cómo listar cuentas.
  - Solo la variable `MATRIZ_ACCOUNTS`, leída en los settings y expuesta por `GET /accounts` — es lo más simple; no se puede editar sin reiniciar y no admite alias.
- [x] ¿El listado muestra las órdenes de todas las cuentas del caché o solo las de una cuenta elegida? — **Resolved:** **Una sola cuenta, elegida en un `Select` arriba de la tabla.** Es la única opción planteada. Además, con una sola llamada por refresco, los errores se manejan de forma directa (EB-5, EB-10) y no hace falta resolver fallas parciales por cuenta.
  - Una sola cuenta, elegida en un `Select` arriba de la tabla — hay una sola llamada y el manejo de errores es simple; el usuario no ve todas las órdenes juntas.
- [x] ¿Qué órdenes trae el listado por defecto? — **Resolved:** **`get_all_orders` sin filtro**: es lo más simple. La contra es que, con muchas órdenes finales, cuesta encontrar las activas.

Elijo esta opción porque los requisitos dan por hecho que las órdenes finales se ven en la tabla. EB-12 pide que no tengan «Cancelar» habilitado, EB-8 detiene el refresco cuando todas son finales y EB-15 exige que la fila cancelada muestre su nuevo estado. Con `get_active_orders`, esas filas desaparecerían de la tabla.
  - Solo `get_active_orders` — la tabla queda más corta y el refresco casi nunca se detiene; las órdenes ejecutadas o canceladas desaparecen sin dejar rastro.
  - `get_all_orders` sin filtro — es lo más simple; con muchas órdenes finales cuesta encontrar las activas.
- [x] ¿De dónde salen los instrumentos para el selector de «Activo»? — **Resolved:** Los instrumentos salen de `get_all_instruments` de `matriz-client`. Se llaman solo a través de `list_instruments` en `broker/src/broker/matriz_gateway.py`, que devuelve tipos propios del repo (`symbol`, `market_id`), y el backend los expone en `GET /instruments`. Así se confirma PA-8: es metadata para dar de alta órdenes, no market data, y `market-data-client` sigue solo en el worker. Como el catálogo casi no cambia durante el día, el backend lo guarda en memoria del proceso con un TTL (p. ej. 1 h) sobre la misma instancia que hace login al primer uso. En el frontend, la query usa un `staleTime` largo y no se refresca periódicamente. Si Matriz falla, `GET /instruments` responde `502` con un mensaje legible y el selector muestra el error y bloquea el envío, como pide EB-23.

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Qué componente opera órdenes con Matriz y dónde queda el único módulo que importa `matriz_client`?** — El backend opera las órdenes de forma síncrona: listar, crear y cancelar pasan por endpoints FastAPI. Se descarta la cola en Postgres con el worker porque no da los errores inmediatos que piden EB-16 y EB-32. El único módulo que importa `matriz_client` pasa a un nuevo paquete del workspace `uv`, `matriz-broker` (`import broker`, layout `src/`, con `py.typed`), en `broker/src/broker/matriz_gateway.py`. Ese módulo absorbe el actual `worker/src/worker/matriz_gateway.py` y suma `list_orders`, `new_order`, `cancel_order` y `list_instruments` con tipos propios del repo. `matriz-backend` y `matriz-worker` dependen de `matriz-broker`, y `matriz-client==0.3.0` se declara solo en ese paquete. Así el worker conserva su `login()` (UB-7) sin que el worker dependa del backend ni el backend del worker. Además, `docker-compose.yml` pasa las variables `MATRIZ_*` al servicio `backend`, y `CLAUDE.md` se actualiza para indicar este módulo como único punto de acceso a Matriz.
- **Si el backend usa `matriz-client`, ¿cómo maneja la sesión con Matriz?** — **Login al primer uso, en diferido, con la instancia guardada en caché.** Así el backend arranca y `GET /health` sigue respondiendo (UB-4) aunque Matriz esté caído, y se evita un login por request que podría chocar contra el rate limit. Además coincide con la propuesta de PA-10: una instancia por proceso, inyectada como dependencia de FastAPI y reemplazable por el fake en los tests.
- **¿Dónde vive el caché de cuentas y cómo se llena?** — Recomiendo quedarse con la variable `MATRIZ_ACCOUNTS`: los settings la leen y `GET /accounts` la expone. Es lo más simple. No se puede editar sin reiniciar y no admite alias. Es la única opción planteada y alcanza para EB-20 y EB-21 sin sumar una tabla, una migración Alembic ni un proceso que siembre datos, porque `matriz-client` no ofrece cómo listar cuentas.
- **¿El listado muestra las órdenes de todas las cuentas del caché o solo las de una cuenta elegida?** — **Una sola cuenta, elegida en un `Select` arriba de la tabla.** Es la única opción planteada. Además, con una sola llamada por refresco, los errores se manejan de forma directa (EB-5, EB-10) y no hace falta resolver fallas parciales por cuenta.
- **¿Qué órdenes trae el listado por defecto?** — **`get_all_orders` sin filtro**: es lo más simple. La contra es que, con muchas órdenes finales, cuesta encontrar las activas.
- **¿De dónde salen los instrumentos para el selector de «Activo»?** — Los instrumentos salen de `get_all_instruments` de `matriz-client`. Se llaman solo a través de `list_instruments` en `broker/src/broker/matriz_gateway.py`, que devuelve tipos propios del repo (`symbol`, `market_id`), y el backend los expone en `GET /instruments`. Así se confirma PA-8: es metadata para dar de alta órdenes, no market data, y `market-data-client` sigue solo en el worker. Como el catálogo casi no cambia durante el día, el backend lo guarda en memoria del proceso con un TTL (p. ej. 1 h) sobre la misma instancia que hace login al primer uso. En el frontend, la query usa un `staleTime` largo y no se refresca periódicamente. Si Matriz falla, `GET /instruments` responde `502` con un mensaje legible y el selector muestra el error y bloquea el envío, como pide EB-23.
