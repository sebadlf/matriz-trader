🔧 **Read** `quiero-generar-un-nuevo-utils-llamado-utils-instrument/requirements.md`1	# Requirements: utils_instrument — tipo de instrumento y división de precio por 100
2	
3	## Introduction
4	
5	Se agrega al backend un módulo `utils_instrument.py` con dos funciones:
6	
7	- `get_instrument_type`: recibe un instrumento (símbolo y `market_id`) y devuelve su tipo como un miembro de un enum (`InstrumentType`). Para resolverlo usa como fuente el detalle de instrumentos de `matriz-client` (`get_instruments_details`, que devuelve `list[InstrumentDetail]`). La clasificación sale del campo `InstrumentDetail.cficode` (ISO 10962).
8	- `should_divide_price_by_100`: recibe un `InstrumentT
… (truncated)🔧 **Read** `quiero-generar-un-nuevo-utils-llamado-utils-instrument/plan.md`1	# Plan: utils_instrument — tipo de instrumento y división de precio por 100
2	
3	> Agregar `InstrumentType` + `should_divide_price_by_100` (dominio puro) y `get_instrument_type` (servicio sobre `matriz-client`, con caché de 10 minutos), sin tocar la API HTTP. Appetite: S. Risk: low.
4	
5	## Approach
6	
7	```mermaid
8	flowchart LR
9	  A["Llamador: symbol + market_id='ROFX'"] --> B["services/utils_instrument.get_instrument_type"]
10	  B -->|"hit vigente menor a 10 min"| E["InstrumentType"]
11	  B -->|"miss o vencido"| C["AsyncClient.get_instrument_detail(symbol, market_id)"]
12	  C --> D["doma
… (truncated)🔧 **Read** `domain/utils_instrument.py`1	"""Tipo de instrumento a partir del código CFI (ISO 10962) y regla de división del precio."""
2	
3	from enum import StrEnum, unique
4	from types import MappingProxyType
5	from typing import Final, assert_never
6	
7	
8	@unique
9	class InstrumentType(StrEnum):
10	    """Nombres estables: renombrar un miembro es un cambio incompatible."""
11	
12	    ACCION = "ACCION"
13	    CEDEAR = "CEDEAR"
14	    BONO = "BONO"
15	    OBLIGACION_NEGOCIABLE = "OBLIGACION_NEGOCIABLE"
16	    LETRA = "LETRA"
17	    FUTURO = "FUTURO"
18	    OPCION_SOBRE_ACCION = "OPCION_SOBRE_ACCION"
19	    OPCION_SOBRE_FUTURO = "O
… (truncated)🔧 **Read** `services/utils_instrument.py`1	"""Tipo de instrumento de Matriz, resuelto con `matriz-client` y cacheado 10 minutos.
2	
3	Consulta un solo instrumento con `get_instrument_detail(symbol, market_id)`, lo clasifica
4	con la tabla CFI pura de `app.domain.utils_instrument` y guarda el resultado en memoria.
5	Las excepciones de `matriz-client` y de red se propagan sin tocar (AC-7).
6	"""
7	
8	from dataclasses import dataclass
9	from datetime import datetime, timedelta
10	from typing import Final, Protocol
11	
12	import structlog
13	from matriz_client import InstrumentDetail, MarketId
14	
15	from app.core.clock import Clock, Sys
… (truncated)🔧 **Bash**

```bash
git diff backend/app/domain/errors.py && grep -c "def test_" backend/tests/test_utils_instrument_domain.py backend/tests/test_utils_instrument_service.py
```diff --git a/backend/app/domain/errors.py b/backend/app/domain/errors.py
index 8965e44..0d9149d 100644
--- a/backend/app/domain/errors.py
+++ b/backend/app/domain/errors.py
@@ -19,3 +19,17 @@ class MarketDataUnavailableError(DomainError):
 
     status: ClassVar[int] = 502
     title: ClassVar[str] = "Market data no disponible"
+
+
+class InstrumentNotFoundError(DomainError):
+    """Matriz no devolvió un instrumento con ese `symbol` y `market_id` (AC-6)."""
+
+    status: ClassVar[int] = 404
+    title: ClassVar[str] = "Instrumento no encontrado"
+
+
+class UnclassifiedInstrumentError(DomainE
… (truncated)## Overview

Se agregó el módulo `utils_instrument` al backend. Obtiene el tipo de un instrumento de Matriz a partir de su código CFI y como un enum tipado (`InstrumentType`), y dice si el precio de ese tipo se divide por 100. No hay cambios en la API HTTP, en `openapi.json`, en el frontend ni en la base de datos.

## Changes

- **Dominio (puro, sin I/O):** el enum `InstrumentType` tiene 8 miembros. Una tabla de CFI a tipo se compara por igualdad exacta e incluye `DYXTXR` → `LETRA`. `should_divide_price_by_100` devuelve `True` solo para `BONO`, `OBLIGACION_NEGOCIABLE` y `LETRA`. Usa un `match` exhaustivo con `assert_never`, así mypy strict falla si se agrega un tipo nuevo sin regla. Como se decidió, se eliminó `DESCONOCIDO`: un instrumento que no se puede clasificar lanza un error en lugar de devolver un tipo.
- **Errores:** dos subclases nuevas de `DomainError`:
  - `InstrumentNotFoundError` (404), cuando el detalle no coincide con el símbolo y el mercado pedidos.
  - `UnclassifiedInstrumentError` (422), cuando el CFI es `None` o no está en la tabla. Antes de lanzarlo se registra un log `warning` `instrument_type_unclassified`.
- **Servicio:** `get_instrument_type` consulta un solo instrumento con `get_instrument_detail(symbol, market_id)`, a través de un `Protocol` que en los tests se reemplaza por un doble. Usa `"ROFX"` por defecto y deja pasar sin tocar las excepciones de `matriz-client` y de red. Guarda el tipo resuelto 10 minutos en un caché en memoria que mide el tiempo con el `Clock` inyectable; los errores no se guardan.
- **Tests:** 11 tests de dominio (tabla CFI, regla de división, exhaustividad y determinismo con Hypothesis) y 9 de servicio (match exacto, `ROFX` por defecto, errores tipados, propagación de excepciones, log y vencimiento del caché), todos sin red.

## Files

- `backend/app/domain/utils_instrument.py`: nuevo. Contiene `InstrumentType`, `CFI_TO_INSTRUMENT_TYPE`, `classify_cficode` y `should_divide_price_by_100`. Vive en el dominio para que el enum y la regla se puedan reutilizar sin importar `matriz_client`.
- `backend/app/domain/errors.py`: agrega `InstrumentNotFoundError` y `UnclassifiedInstrumentError`, para que un instrumento inexistente o sin clasificar dé un error tipado.
- `backend/app/services/utils_instrument.py`: nuevo. Contiene `InstrumentDetailSource` (Protocol), `InstrumentTypeCache` (10 minutos) y `get_instrument_type`, que es la consulta a Matriz más la clasificación y el caché.
- `backend/tests/test_utils_instrument_domain.py`: nuevo. Prueba la tabla CFI, la regla de división y la exhaustividad del enum (AC-1, AC-4, AC-8 a AC-11).
- `backend/tests/test_utils_instrument_service.py`: nuevo. Prueba `get_instrument_type` con una fuente fake y un reloj fijo (AC-2 a AC-7 y el caché).
- `.octo/specs/quiero-generar-un-nuevo-utils-llamado-utils-instrument/requirements.md`: historias, criterios EARS y decisiones resueltas (tabla CFI, caché de 10 minutos, sin `DESCONOCIDO`, propagar errores).
- `.octo/specs/quiero-generar-un-nuevo-utils-llamado-utils-instrument/plan.md`: dónde va cada pieza (dominio y servicio), los contratos, los riesgos, la verificación por criterio y las tareas T1 a T4.
- `.octo/specs/quiero-generar-un-nuevo-utils-llamado-utils-instrument/tasks.md`: las tareas del spec, marcadas como completadas.

**Notas abiertas del plan:**
- Confirmar el nombre `LETRA` para `DYXTXR`.
- Decidir si un `PrimaryAPIError` por símbolo inexistente debe traducirse a `InstrumentNotFoundError`.
- AC-2 y AC-5 en `requirements.md` todavía describen el diseño anterior (buscar en la lista completa y devolver `DESCONOCIDO`) y hay que reescribirlos.