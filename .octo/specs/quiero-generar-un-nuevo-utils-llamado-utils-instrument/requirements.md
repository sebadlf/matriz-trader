# Requirements: utils_instrument — tipo de instrumento y división de precio por 100

## Introduction

Se agrega al backend un módulo `utils_instrument.py` con dos funciones:

- `get_instrument_type`: recibe un instrumento (símbolo y `market_id`) y devuelve su tipo como un miembro de un enum (`InstrumentType`). Para resolverlo usa como fuente el detalle de instrumentos de `matriz-client` (`get_instruments_details`, que devuelve `list[InstrumentDetail]`). La clasificación sale del campo `InstrumentDetail.cficode` (ISO 10962).
- `should_divide_price_by_100`: recibe un `InstrumentType` y devuelve `True` si el precio de ese tipo de instrumento debe dividirse por 100 y `False` si no.

El enum existe para pasar el tipo como parámetro tipado a otras funciones (por ejemplo, `should_divide_price_by_100`) en lugar de usar strings sueltos.

Por las capas del backend (`backend/CLAUDE.md`, import-linter), la función que consulta `matriz-client` no puede vivir en `app.domain`: este importa `matriz_client` (contrato «Dominio puro»). El enum `InstrumentType` y `should_divide_price_by_100` son reglas puras, sin I/O. La ubicación exacta de cada pieza se decide en el plan (ver Open Questions).

Mapeo de CFI a tipo propuesto para este borrador (a confirmar en Open Questions):

| `cficode` | `InstrumentType` | ¿Dividir precio por 100? |
|---|---|---|
| `ESXXXX` | `ACCION` | No |
| `EMXXXX` | `CEDEAR` | No |
| `DBXXXX` | `BONO` | Sí |
| `DBXXFR` | `OBLIGACION_NEGOCIABLE` | Sí |
| `FXXXSX` | `FUTURO` | No |
| `OCASPS`, `OPASPS` | `OPCION_SOBRE_ACCION` | No |
| `OCAFXS`, `OPAFXS` | `OPCION_SOBRE_FUTURO` | No |
| ausente o desconocido | `DESCONOCIDO` | No |

## User Stories

- US-1: As a desarrollador del backend, I want obtener el tipo de un instrumento como un miembro de un enum a partir de su símbolo, so that pueda pasarlo tipado a otras funciones sin comparar strings ni códigos CFI.
- US-2: As a desarrollador del backend, I want saber, a partir del tipo de instrumento, si su precio debe dividirse por 100, so that convierta bien los precios cotizados cada 100 nominales sin repetir la regla en cada lugar.
- US-3: As a operador de estrategias, I want que un instrumento que no se puede clasificar nunca se trate en silencio como un tipo conocido, so that un precio no se escale mal por una clasificación inventada.

## Acceptance Criteria (EARS notation)

- AC-1: WHEN `get_instrument_type` se llama con un símbolo y un `market_id` cuyo `InstrumentDetail` tiene un `cficode` de la tabla de la Introduction THEN the system SHALL devolver el miembro de `InstrumentType` que esa tabla le asigna. (US-1)
- AC-2: WHEN `get_instrument_type` se llama THEN the system SHALL buscar el instrumento entre los `InstrumentDetail` de `get_instruments_details` comparando `instrumentId.symbol` e `instrumentId.marketId` por igualdad exacta. (US-1)
- AC-3: WHEN `get_instrument_type` se llama sin `market_id` THEN the system SHALL usar `"ROFX"`, el mismo valor por defecto que `matriz-client`. (US-1)
- AC-4: WHEN `get_instrument_type` devuelve un valor THEN the system SHALL devolver siempre un miembro de `InstrumentType`, nunca un `str`, un código CFI crudo ni `None`. (US-1)
- AC-5: IF el `InstrumentDetail` encontrado tiene `cficode` igual a `None` o un código que no está en la tabla de la Introduction THEN the system SHALL devolver `InstrumentType.DESCONOCIDO` y registrar un log estructurado de nivel `warning` con `symbol`, `market_id` y el `cficode` recibido. (US-3)
- AC-6: IF ningún `InstrumentDetail` de `get_instruments_details` coincide con el símbolo y el `market_id` pedidos THEN the system SHALL lanzar una subclase de `DomainError` que nombre el símbolo y el `market_id`, sin devolver un tipo. (US-3)
- AC-7: IF `get_instruments_details` lanza una excepción de `matriz-client` THEN the system SHALL propagarla, o traducirla a un error tipado, sin devolver ningún `InstrumentType`. (US-3)
- AC-8: WHEN `should_divide_price_by_100` se llama con `InstrumentType.BONO` o `InstrumentType.OBLIGACION_NEGOCIABLE` THEN the system SHALL devolver `True`. (US-2)
- AC-9: WHEN `should_divide_price_by_100` se llama con cualquier otro miembro de `InstrumentType`, incluido `DESCONOCIDO`, THEN the system SHALL devolver `False`. (US-2, US-3)
- AC-10: WHEN `should_divide_price_by_100` se llama THEN the system SHALL resolver el resultado sin I/O (sin llamar a `matriz-client`, la red ni la base de datos) y devolver el mismo valor para la misma entrada. (US-2)
- AC-11: WHEN se agrega un miembro nuevo a `InstrumentType` sin definir su regla de división THEN the system SHALL fallar el gate del backend (test o chequeo de exhaustividad de mypy) en lugar de asumir un valor por defecto en silencio. (US-2, US-3)

## Out of Scope

- Hacer la división del precio. `should_divide_price_by_100` solo responde `True` o `False`; convertir precios es trabajo de quien la llame.
- Exponer el tipo de instrumento en la API HTTP (endpoint nuevo, cambio de `openapi.json` o del cliente Orval) o mostrarlo en el frontend.
- Persistir los detalles de instrumentos en PostgreSQL o agregar modelos ORM o migraciones.
- Usar `priceConvertionFactor`, `contractMultiplier` u otros campos de `InstrumentDetail` para decidir la división.
- Soportar mercados distintos de los que acepta `matriz-client` (hoy solo `ROFX`).

## Non-Functional Requirements

- Todas las funciones y miembros nuevos tienen anotaciones de tipo y pasan `mypy --strict` y Ruff con `ANN` — lo verifica `scripts/gate.sh backend full`.
- Ubicación y dependencias según las capas del backend: `InstrumentType` y `should_divide_price_by_100` no importan `matriz_client`, `httpx`, `fastapi` ni `sqlalchemy` — lo verifica `uv run lint-imports`.
- Los tests no hacen llamadas de red reales: `get_instruments_details` se reemplaza por un doble de prueba.
- Cada criterio AC-1 a AC-11 tiene al menos un test en `backend/tests/` y la cobertura del backend se mantiene en el 85 % o más.
- Los nombres de los miembros de `InstrumentType` son estables: un cambio de nombre se trata como un cambio incompatible.

## Open Questions
- [x] ¿La tabla CFI → `InstrumentType` de la Introduction es la definitiva, o hay que sumar tipos que también se dividen por 100? — **Resolved:** Se dividen por 100 los instrumentos con cfi DBXXFR, DBXXXX y DYXTXR
  - Tabla tal cual (solo `BONO` y `OBLIGACION_NEGOCIABLE` dividen) — alcance mínimo; letras y otros instrumentos de deuda caen en `DESCONOCIDO` y no se dividen.
  - Sumar también cauciones y pases (`LRXXXX`) como tipo propio sin división — el enum queda más completo, pero hay más códigos que validar.
- [x] ¿Cómo debe evitar `get_instrument_type` traer todos los instrumentos del mercado en cada llamada? — **Resolved:** Pasar el symbol completo como parametro. Y guardar en cache el valor resuelto por 10 minutos
  - Usar `get_instrument_detail(symbol, market_id)` para un solo instrumento — sin estado ni caché, pero hace una llamada de red por consulta.
  - Recibir la lista `list[InstrumentDetail]` ya obtenida como parámetro — función pura y fácil de testear, pero quien la llama se ocupa de traerla.
  - Llamar a `get_instruments_details` en cada consulta, sin caché — lo más simple, pero lento y costoso si se usa en un loop.
- [ ] ¿Dónde viven las piezas del módulo `utils_instrument`?
  - Un solo archivo en `app/services/utils_instrument.py` — un único import para quien lo usa, pero el dominio no puede reutilizar el enum.
- [x] ¿Cómo se comporta `get_instrument_type` cuando no puede clasificar el instrumento? — **Resolved:** Ambos casos lanzan `DomainError` y se elimina `DESCONOCIDO` del enum — más estricto, nunca opera con un tipo incierto, pero un CFI nuevo frena cualquier uso.
  - Ambos casos lanzan `DomainError` y se elimina `DESCONOCIDO` del enum — más estricto, nunca opera con un tipo incierto, pero un CFI nuevo frena cualquier uso.
  - Ambos casos devuelven `DESCONOCIDO` — nunca lanza error, pero un símbolo mal escrito pasa en silencio.
- [x] ¿Qué hace `get_instrument_type` cuando `get_instruments_details` falla (AC-7)? — **Resolved:** Propaga la excepción de `matriz-client` sin tocarla — menos código, pero los servicios que la llaman quedan acoplados a los errores de la librería.
  - Propaga la excepción de `matriz-client` sin tocarla — menos código, pero los servicios que la llaman quedan acoplados a los errores de la librería.
- [x] ¿El mapeo de CFI compara el código completo o un patrón por posiciones? — **Resolved:** **Igualdad exacta contra los códigos de la tabla:** es determinista y simple. Además, como ya se decidió que un CFI que no está en la tabla lanza `DomainError`, cualquier variante no prevista falla de forma visible en lugar de clasificarse mal y escalar un precio por error.
  - Igualdad exacta contra los códigos de la tabla — determinista y simple, pero cualquier variante de atributo cae en `DESCONOCIDO`.

1. **Tabla de tipos y división por 100.** ¿Es correcta la tabla de la Introduction? En particular: ¿solo bonos (`DBXXXX`) y obligaciones negociables (`DBXXFR`) se dividen por 100, o también letras, cauciones, futuros u opciones de algún subyacente? ¿Te sirven los nombres de los miembros del enum (`ACCION`, `CEDEAR`, `BONO`, …) o preferís otros?
2. **Costo de la consulta.** `get_instruments_details` trae todos los instrumentos del mercado en cada llamada. ¿`get_instrument_type` debe cachear el resultado en memoria (y con qué vigencia), recibir la lista ya obtenida como parámetro, o usar `get_instrument_detail(symbol, market_id)` para consultar un solo instrumento?
3. **Ubicación del módulo.** El backend no tiene una capa `utils`. Propuesta: `InstrumentType` y `should_divide_price_by_100` en `app/domain/utils_instrument.py` (puro) y `get_instrument_type` en `app/services/utils_instrument.py` (usa `matriz-client`). ¿O preferís un solo archivo en `app/services/`, aunque la regla pura quede fuera del dominio?
4. **Instrumento sin clasificar.** ¿Es correcto que un CFI desconocido devuelva `DESCONOCIDO` (AC-5) y que un símbolo inexistente lance error (AC-6), o preferís que ambos casos lancen error?

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿La tabla CFI → `InstrumentType` de la Introduction es la definitiva, o hay que sumar tipos que también se dividen por 100?** — Se dividen por 100 los instrumentos con cfi DBXXFR, DBXXXX y DYXTXR
- **¿Cómo debe evitar `get_instrument_type` traer todos los instrumentos del mercado en cada llamada?** — Pasar el symbol completo como parametro. Y guardar en cache el valor resuelto por 10 minutos
- **¿Cómo se comporta `get_instrument_type` cuando no puede clasificar el instrumento?** — Ambos casos lanzan `DomainError` y se elimina `DESCONOCIDO` del enum — más estricto, nunca opera con un tipo incierto, pero un CFI nuevo frena cualquier uso.
- **¿Qué hace `get_instrument_type` cuando `get_instruments_details` falla (AC-7)?** — Propaga la excepción de `matriz-client` sin tocarla — menos código, pero los servicios que la llaman quedan acoplados a los errores de la librería.
- **¿El mapeo de CFI compara el código completo o un patrón por posiciones?** — **Igualdad exacta contra los códigos de la tabla:** es determinista y simple. Además, como ya se decidió que un CFI que no está en la tabla lanza `DomainError`, cualquier variante no prevista falla de forma visible en lugar de clasificarse mal y escalar un precio por error.
