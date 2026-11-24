# Requirements: tabla filtrable con la market data de los instrumentos suscriptos y spread bid/ask en porcentaje

## Introduction

Hoy el backend solo expone `GET /api/health` y el frontend no muestra datos de mercado. La configuración de `market-data-client` (v0.7.1) ya está tipada en `Settings` (`backend/app/core/config.py`: `market_data_client_id`, `market_data_client_secret`, `market_data_audience`, `market_data_auth0_token_url`, `market_data_base_url`), pero ningún código construye el cliente.

Esta feature agrega la primera lectura de datos de mercado de punta a punta:

1. Un endpoint del backend que obtiene, mediante `market-data-client`, el último snapshot de **todos** los instrumentos suscriptos (los símbolos activos del catálogo del servicio de market data) y lo devuelve con tipos del dominio (`Decimal` → `string`, fechas UTC).
2. Un campo calculado que no viene de la librería: el **spread entre ask (mejor oferta) y bid (mejor compra) expresado en porcentaje**.
3. Una pantalla del frontend con una tabla que muestra esos datos y permite filtrarlos.

Datos que provee la librería por instrumento (`MarketDataSnapshot`, relevados del código instalado):

| Campo de la librería | Significado | Columna propuesta |
|---|---|---|
| `symbol` | Símbolo del instrumento | Símbolo |
| `market_id` | Mercado | Mercado |
| `market_data.BI[0]` (`price`, `size`) | Mejor bid | Bid / Cant. bid |
| `market_data.OF[0]` (`price`, `size`) | Mejor ask (oferta) | Ask / Cant. ask |
| `market_data.LA` (`price`, `size`, `date`) | Último operado | Último / Cant. último / Hora último |
| `market_data.OP` | Apertura | Apertura |
| `market_data.HI` | Máximo | Máximo |
| `market_data.LO` | Mínimo | Mínimo |
| `market_data.CL.price` | Cierre anterior | Cierre |
| `market_data.SE.price` | Settlement | Settlement |
| `market_data.OI.size` | Interés abierto | Interés abierto |
| `market_data.TV` | Volumen operado | Volumen |
| `staleness_seconds` | Antigüedad del dato según el servicio | Antigüedad (s) |
| `received_at` | Momento en que el cliente recibió el snapshot | — (se usa para "última actualización") |

La librería entrega precios como `float`; el backend los convierte a `Decimal` (vía `str`) antes de exponerlos, según `backend/CLAUDE.md`.

## User Stories

- US-1: As a trader manual, I want ver en una tabla la market data actual de todos los instrumentos suscriptos, so that pueda evaluar el mercado de un vistazo antes de armar una orden.
- US-2: As a trader manual, I want ver para cada instrumento el spread entre ask y bid expresado en porcentaje, so that pueda comparar la liquidez de instrumentos con precios de distinta magnitud.
- US-3: As a trader manual, I want filtrar la tabla por símbolo y por mercado, so that pueda concentrarme en los instrumentos que me interesan cuando hay muchos suscriptos.
- US-4: As a operador de estrategias, I want que un fallo del servicio de market data se informe de forma explícita y trazable, so that nunca confunda un dato faltante o desactualizado con un dato real.
- US-5: As a trader manual, I want que la tabla se actualice sola mientras la tengo abierta y me indique cuándo fue la última actualización, so that no opere mirando precios viejos.

## Acceptance Criteria (EARS notation)

- AC-1: WHEN el frontend llama a `GET /api/market-data` THEN the system SHALL responder `200` con una fila por cada instrumento suscripto en el servicio de market data (símbolos con `active = true`), sin omitir ninguno aunque el servicio pagine la respuesta. (US-1)
- AC-2: WHEN el backend arma cada fila THEN the system SHALL incluir `symbol`, `market_id`, precio y cantidad del mejor bid, precio y cantidad del mejor ask, precio, cantidad y fecha del último operado, apertura, máximo, mínimo, cierre, settlement, interés abierto, volumen operado, `staleness_seconds` y la fecha en que se obtuvo el snapshot. (US-1)
- AC-3: WHEN el backend serializa precios, cantidades, volúmenes y el spread THEN the system SHALL convertirlos a `Decimal` a partir de su representación `str` y exponerlos en el JSON como `string`, nunca como número de punto flotante. (US-1)
- AC-4: WHEN el backend serializa una fecha THEN the system SHALL exponerla en ISO 8601 con zona horaria UTC. (US-1)
- AC-5: IF la librería no informa un valor para un campo de un instrumento (`None`, libro vacío o entrada ausente) THEN the system SHALL devolver `null` en ese campo y nunca `"0"`. (US-1)
- AC-6: IF un instrumento suscripto no tiene ningún dato de mercado THEN the system SHALL incluir igualmente su fila, con `symbol` y `market_id` y el resto de los campos en `null`. (US-1)
- AC-7: WHEN se exporta el contrato de la API THEN the system SHALL declarar la ruta con `operation_id` `listMarketData`, `tags=["market-data"]` y un esquema de respuesta definido en `app/schemas/`. (US-1)
- AC-8: WHEN el mejor bid y el mejor ask de un instrumento tienen precio mayor que cero THEN the system SHALL calcular `spread_pct = (ask − bid) / ((ask + bid) / 2) × 100` con aritmética `Decimal` y redondearlo a 4 decimales con `ROUND_HALF_EVEN`. (US-2)
- AC-9: IF falta el mejor bid o el mejor ask, o alguno de sus precios es menor o igual que cero THEN the system SHALL devolver `spread_pct = null` y la tabla SHALL mostrar `—` en esa celda. (US-2)
- AC-10: IF el mejor ask es menor que el mejor bid (libro cruzado) THEN the system SHALL devolver el `spread_pct` negativo que resulte de la fórmula de AC-8, sin recortarlo a cero. (US-2)
- AC-11: WHEN el usuario navega a la ruta `/market-data` THEN the system SHALL mostrar una tabla con una fila por instrumento y una columna por cada campo de AC-2 más la columna `Spread %`. (US-1)
- AC-12: WHEN la tabla muestra un precio, cantidad o spread THEN the system SHALL formatearlo a partir del `string` recibido sin convertirlo a `number` de JavaScript, y mostrar el spread con 2 decimales seguido de `%`. (US-2)
- AC-13: WHILE la primera carga de datos está en curso THE system SHALL mostrar un indicador de carga en lugar de la tabla vacía. (US-1)
- AC-14: IF el backend devuelve una lista vacía THEN the system SHALL mostrar un estado vacío con el texto "No hay instrumentos suscriptos". (US-1)
- AC-15: WHEN el usuario escribe texto en el filtro de símbolo THEN the system SHALL mostrar solo las filas cuyo símbolo contiene ese texto, sin distinguir mayúsculas de minúsculas. (US-3)
- AC-16: WHEN el usuario selecciona uno o más mercados en el filtro de mercado THEN the system SHALL mostrar solo las filas cuyo `market_id` está entre los seleccionados, y SHALL ofrecer como opciones solo los `market_id` presentes en los datos. (US-3)
- AC-17: WHEN el usuario combina el filtro de símbolo y el de mercado THEN the system SHALL mostrar solo las filas que cumplen ambos. (US-3)
- AC-18: WHEN el usuario cambia un filtro THEN the system SHALL reflejarlo en los query params de la URL, de modo que al abrir esa URL se apliquen los mismos filtros. (US-3)
- AC-19: IF los filtros activos no dejan ninguna fila THEN the system SHALL mostrar el texto "Ningún instrumento coincide con los filtros" y una acción "Limpiar filtros" que los quita. (US-3)
- AC-20: IF `market-data-client` falla al obtener los datos (error de autenticación, timeout, error de red o respuesta 5xx) THEN the system SHALL responder `502` con `application/problem+json` (`ProblemDetails`) que incluye `correlation_id`, sin devolver datos parciales. (US-4)
- AC-21: IF falla el backend al obtener los datos THEN the system SHALL registrar un log estructurado con `correlation_id` y el tipo de error, sin incluir `market_data_client_secret` ni el token de acceso. (US-4)
- AC-22: IF la carga de datos falla y no hay datos previos THEN the system SHALL mostrar un `Alert` de error con el `title`, el `detail` y el `correlationId` del `ApiError`, y un botón "Reintentar". (US-4)
- AC-23: WHILE la pantalla `/market-data` está abierta THE system SHALL volver a pedir los datos cada 5 segundos, manteniendo los filtros aplicados y sin reemplazar la tabla por el indicador de carga. (US-5)
- AC-24: WHILE la pantalla muestra datos THE system SHALL mostrar la fecha y hora de la última actualización exitosa. (US-5)
- AC-25: IF una actualización falla después de una carga exitosa THEN the system SHALL conservar los últimos datos en la tabla y mostrar un aviso de error que indica la hora de la última actualización exitosa. (US-5)
- AC-26: WHEN la tabla muestra la columna de antigüedad THEN the system SHALL mostrar `staleness_seconds` tal como lo informa el servicio, o `—` si es `null`. (US-4)

## Out of Scope

- Suscribir o desuscribir instrumentos (alta/baja de símbolos en el catálogo de market data).
- Streaming en tiempo real (WebSocket/SSE): la actualización es por consulta periódica.
- Profundidad del libro más allá del mejor bid y mejor ask.
- Datos históricos, gráficos o series de tiempo.
- Persistir la market data en PostgreSQL: no hay modelos ORM ni migraciones nuevas.
- Enviar órdenes desde la tabla o usar `matriz-client`.
- Ordenamiento de columnas, filtros por rango numérico (spread, precio, volumen) y columnas configurables por el usuario.
- Paginación de la tabla en el frontend.

## Non-Functional Requirements

- Ningún precio, cantidad, volumen o spread pasa por `float` después del punto de entrada de la librería: el cálculo del spread vive en `app/domain/` sin I/O y se cubre con tests de propiedades (Hypothesis).
- El backend no hace más de `⌈N / tamaño de página⌉` llamadas a `/marketdata` por request, donde `N` es la cantidad de instrumentos suscriptos.
- La tabla renderiza al menos 500 filas sin errores y la pantalla pasa axe (WCAG 2.2 AA) en `scripts/gate.sh e2e`.
- Los secretos (`market_data_client_secret`, access token) no aparecen en logs, respuestas ni `repr` de objetos.
- `backend/openapi.json` y `frontend/src/api/generated/` se regeneran y commitean juntos; el frontend consume el endpoint solo vía el hook generado por Orval.
- Pasan `scripts/gate.sh changed full` (cobertura backend ≥ 85 %, frontend ≥ 70 %, `size-limit`) y `scripts/gate.sh e2e`.

## Open Questions
- [x] ¿Qué fuente define los "instrumentos suscriptos" que lista la tabla? — **Resolved:** `get_market_data(active=True)` del catálogo de market data — una sola fuente y una llamada paginada, pero puede incluir símbolos que el usuario no opera
  - `get_market_data(active=True)` del catálogo de market data — una sola fuente y una llamada paginada, pero puede incluir símbolos que el usuario no opera
  - Suscripciones de Matriz vía `matriz-client` — coincide con la cuenta de trading, pero suma una dependencia y credenciales que hoy quedan fuera de alcance
- [x] ¿Sobre qué base se calcula `spread_pct`? — **Resolved:** Precio medio `(ask − bid) / ((ask + bid) / 2) × 100` — simétrico y estándar para comparar liquidez
  - Precio medio `(ask − bid) / ((ask + bid) / 2) × 100` — simétrico y estándar para comparar liquidez
  - Bid `(ask − bid) / bid × 100` — muestra el costo de entrar comprando al ask y salir vendiendo al bid
  - Ask `(ask − bid) / ask × 100` — siempre es el valor más chico; se usa menos
- [x] ¿Cómo se actualiza la tabla mientras está abierta? — **Resolved:** Polling cada 5 s y además un botón "Actualizar" — refresco automático y control manual, con apenas un poco más de UI
  - Polling cada 5 s y además un botón "Actualizar" — refresco automático y control manual, con apenas un poco más de UI
  - Solo polling cada 5 s — más simple, pero no se puede forzar un refresco
  - Solo el botón "Actualizar" — no genera carga constante, pero los precios pueden quedar viejos sin que el usuario lo note
- [x] ¿Se sigue consultando cuando la pestaña del navegador no está visible? — **Resolved:** Pausar el polling con la pestaña oculta y refrescar al volver — ahorra llamadas al servicio y a Auth0
  - Pausar el polling con la pestaña oculta y refrescar al volver — ahorra llamadas al servicio y a Auth0
  - Seguir con el polling en segundo plano (`refetchIntervalInBackground`) — los datos están al día al volver, a costa de llamadas constantes
- [x] ¿Cómo se construye y cuánto vive el cliente de `market-data-client` en el backend? — **Resolved:** Un cliente nuevo por request — más simple de aislar, pero pide un token a Auth0 en cada request (cada 5 s por pestaña abierta)
  - Un cliente nuevo por request — más simple de aislar, pero pide un token a Auth0 en cada request (cada 5 s por pestaña abierta)
- [x] ¿La tabla tiene que marcar visualmente los datos desactualizados según `staleness_seconds`? — **Resolved:** Solo mostrar el número, como dice AC-26 — no hay que definir un umbral ni una variable de configuración
  - Solo mostrar el número, como dice AC-26 — no hay que definir un umbral ni una variable de configuración

1. **¿Qué significa "instrumentos suscriptos"?** Asumí los símbolos con `active = true` del catálogo del servicio de market data (`get_market_data(active=True)` / `get_symbols(active=True)`). La alternativa es `get_instruments(subscribed=True)` o las suscripciones de Matriz vía `matriz-client`; cambia la fuente de datos.
2. **Fórmula del spread %.** Asumí `(ask − bid) / precio medio × 100`. Las alternativas habituales son dividir por el bid o por el ask. ¿Cuál querés?
3. **Actualización.** Asumí polling cada 5 s mientras la pantalla está abierta. ¿Preferís otro intervalo, un botón de "Actualizar" manual, o ambos?
4. **Filtros.** Asumí filtro por texto de símbolo y por mercado. ¿Necesitás además filtrar por rango de spread u otro campo, u ordenar columnas (hoy fuera de alcance)?

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Qué fuente define los "instrumentos suscriptos" que lista la tabla?** — `get_market_data(active=True)` del catálogo de market data — una sola fuente y una llamada paginada, pero puede incluir símbolos que el usuario no opera
- **¿Sobre qué base se calcula `spread_pct`?** — Precio medio `(ask − bid) / ((ask + bid) / 2) × 100` — simétrico y estándar para comparar liquidez
- **¿Cómo se actualiza la tabla mientras está abierta?** — Polling cada 5 s y además un botón "Actualizar" — refresco automático y control manual, con apenas un poco más de UI
- **¿Se sigue consultando cuando la pestaña del navegador no está visible?** — Pausar el polling con la pestaña oculta y refrescar al volver — ahorra llamadas al servicio y a Auth0
- **¿Cómo se construye y cuánto vive el cliente de `market-data-client` en el backend?** — Un cliente nuevo por request — más simple de aislar, pero pide un token a Auth0 en cada request (cada 5 s por pestaña abierta)
- **¿La tabla tiene que marcar visualmente los datos desactualizados según `staleness_seconds`?** — Solo mostrar el número, como dice AC-26 — no hay que definir un umbral ni una variable de configuración
