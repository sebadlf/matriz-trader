# Tasks — Quiero generar un nuevo utils llamado utils_instrument

### Wave 1
- [x] T1 @backend-expert: Crear `backend/app/domain/utils_instrument.py` con `InstrumentType`, `CFI_TO_INSTRUMENT_TYPE`, `classify_cficode` y `should_divide_price_by_100` (match exhaustivo con `assert_never`), más `backend/tests/test_utils_instrument_domain.py` — _outcome: tabla CFI y regla de división probadas, mypy detecta un miembro sin regla (AC-1, AC-4, AC-8, AC-9, AC-10, AC-11)_
- [x] T2 @backend-expert: Agregar `InstrumentNotFoundError` y `UnclassifiedInstrumentError` en `backend/app/domain/errors.py` — _outcome: dos subclases de `DomainError` con `status`/`title` del plan, importables desde `app.domain.errors` (AC-5, AC-6)_

### Wave 2 (depends on T1, T2)
- [x] T3 @backend-expert: Crear `backend/app/services/utils_instrument.py` con `InstrumentDetailSource`, `InstrumentTypeCache` (TTL 10 min con `Clock`) y `get_instrument_type`, más `backend/tests/test_utils_instrument_service.py` con fuente fake y reloj fijo — _outcome: `get_instrument_type` resuelve por símbolo, usa `ROFX` por defecto, lanza los errores tipados, propaga las excepciones de `matriz-client` y cachea 10 minutos (AC-2, AC-3, AC-4, AC-5, AC-6, AC-7)_

### Wave 3 (depends on T3)
- [x] T4: Correr `scripts/gate.sh changed full` y corregir lo que falle — _outcome: el gate del backend sale con `0`, cobertura ≥ 85 % y `lint-imports` en verde (AC-10, AC-11)_
