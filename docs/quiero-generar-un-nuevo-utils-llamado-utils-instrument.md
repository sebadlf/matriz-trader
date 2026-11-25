# Tipo de instrumento y división de precio por 100

El backend clasifica un instrumento de Matriz en un `InstrumentType` a partir de su código CFI (ISO 10962) y decide si su precio se divide por 100. Todavía no lo usa ningún endpoint ni pantalla: es una utilidad interna para los servicios que conviertan precios.

## Dónde vive cada pieza

| Pieza | Archivo | Capa |
|---|---|---|
| `InstrumentType`, `CFI_TO_INSTRUMENT_TYPE`, `classify_cficode`, `should_divide_price_by_100` | `backend/app/domain/utils_instrument.py` | Dominio puro, sin I/O ni `matriz_client` |
| `InstrumentDetailSource`, `InstrumentTypeCache`, `get_instrument_type` | `backend/app/services/utils_instrument.py` | Servicio, consulta `matriz-client` |
| `InstrumentNotFoundError`, `UnclassifiedInstrumentError` | `backend/app/domain/errors.py` | Errores de dominio (`DomainError`) |

## Tabla CFI

La comparación es por igualdad exacta del código completo.

| `cficode` | `InstrumentType` | ¿Dividir precio por 100? |
|---|---|---|
| `ESXXXX` | `ACCION` | No |
| `EMXXXX` | `CEDEAR` | No |
| `DBXXXX` | `BONO` | Sí |
| `DBXXFR` | `OBLIGACION_NEGOCIABLE` | Sí |
| `DYXTXR` | `LETRA` | Sí |
| `FXXXSX` | `FUTURO` | No |
| `OCASPS`, `OPASPS` | `OPCION_SOBRE_ACCION` | No |
| `OCAFXS`, `OPAFXS` | `OPCION_SOBRE_FUTURO` | No |

`should_divide_price_by_100` solo responde `True` o `False`: dividir el precio es trabajo de quien la llama.

## Uso

```python
from app.domain.utils_instrument import should_divide_price_by_100
from app.services.utils_instrument import get_instrument_type

instrument_type = await get_instrument_type(matriz_client, "AL30")  # market_id="ROFX"
if should_divide_price_by_100(instrument_type):
    ...
```

`source` es cualquier objeto con `get_instrument_detail(symbol, market_id)` (el `AsyncClient` de `matriz-client` o un doble en los tests). Quien llama crea y cierra el cliente.

## Comportamiento

- **Caché:** el tipo resuelto se guarda en memoria por `(market_id, symbol)` durante 10 minutos (`CACHE_TTL`), medidos con el `Clock` inyectable. Los errores no se cachean. El caché por defecto es global por proceso; los tests pasan su propio `InstrumentTypeCache`.
- **Instrumento no encontrado:** si el `instrumentId` del detalle no coincide exactamente con el símbolo y el mercado pedidos (incluido un detalle vacío), lanza `InstrumentNotFoundError` (`404`).
- **CFI sin clasificar:** si `cficode` es `None` o no está en la tabla, registra el log `warning` `instrument_type_unclassified` con `symbol`, `market_id` y `cficode`, y lanza `UnclassifiedInstrumentError` (`422`). No existe un tipo «desconocido»: nunca se opera con una clasificación incierta.
- **Errores de Matriz:** `PrimaryAPIError`, `AuthenticationError`, `MatrizDecodeError` o `httpx.HTTPError` se propagan sin tocar. Un símbolo que Primary rechaza con `status: "ERROR"` llega como `PrimaryAPIError`, no como `InstrumentNotFoundError`.

## Agregar un tipo nuevo

1. Sumar el miembro a `InstrumentType` (los nombres son estables: renombrar uno es un cambio incompatible).
2. Sumar el código a `CFI_TO_INSTRUMENT_TYPE`.
3. Sumar la rama en `should_divide_price_by_100`: si falta, mypy falla por el `assert_never`.
4. Actualizar los tests de `backend/tests/test_utils_instrument_domain.py`.
