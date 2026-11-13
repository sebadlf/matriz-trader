# Tasks — ## Estado actual del repo - La ruta

### Wave 1

- [x] T1: Crear el paquete `matriz-broker` (`broker/pyproject.toml`, `src/broker/{__init__,py.typed,matriz_gateway}.py`, `tests/test_matriz_gateway.py`), registrarlo en `pyproject.toml:5,20,22-26,37`, sumarlo a `scripts/check.sh:30`, recablear dependencias (`worker/pyproject.toml:7,22` quita `matriz-client` y suma `matriz-broker`; `backend/pyproject.toml:5-10,19-20` suma `matriz-broker`) y correr `uv sync` una sola vez (T1 es la única tarea que toca `uv.lock`) — _outcome: `cd broker && uv run pytest` pasa con un `Client` falso cubriendo mapeo de `Order`, `new_order` con `price=None` en MARKET y solo `order_type`/`market_id` como kwargs, redacción de password y login único (EB-27, EB-29, EB-35, EB-37)_
- [x] T2: Crear `frontend/src/pages/orders/orderStatus.ts` y `format.ts` con sus tests — _outcome: `npm test -- orders/` pasa con la clasificación de los 10 estados + nulo/desconocido, `—` para vacíos y `describeApiError` (EB-3, EB-6)_
- [x] T3: Agregar `MATRIZ_ACCOUNTS=` y renombrar la sección Matriz en `.env.example:29-34` — _outcome: `.env.example` documenta `MATRIZ_ACCOUNTS` como lista separada por comas usada por el backend (EB-38, UB-9)_

### Wave 2 (depends on T1)

- [x] T4: Migrar el worker a `broker` (eliminar `worker/src/worker/matriz_gateway.py`, actualizar `runner.py:9`, `__main__.py:12,38`, `tests/test_runner.py:13`, `worker/Dockerfile:19-27`) — _outcome: `cd worker && uv run pytest` pasa y `docker compose build worker` termina OK (UB-7, EB-37)_
- [x] T5: Agregar campos `matriz_*` y `matriz_accounts` en `settings.py`, `backend/src/backend/matriz.py` (provider, `InstrumentCache`, errores) y `backend/Dockerfile:14-22` — _outcome: `backend/tests/test_settings.py` pasa con parseo de `MATRIZ_ACCOUNTS` y con `MATRIZ_*` ausentes sin fallar la carga (EB-38, UB-4)_

### Wave 3 (depends on T5)

- [x] T6: Crear `backend/src/backend/trading.py` con los 5 endpoints, `tests/fake_trading.py`, `tests/test_trading.py`, y cablear en `main.py:31-44` con `allow_methods=["GET","POST"]` — _outcome: `cd backend && uv run pytest tests/test_trading.py tests/test_health.py` pasa cubriendo 200/201/422/502/503, caché de instrumentos y preflight POST (EB-26, EB-27, EB-28, EB-34, EB-35, EB-36, UB-4)_

### Wave 4 (depends on T6)

- [x] T7: Regenerar `frontend/openapi.json` con `uv run python -m backend.export_openapi` y el cliente con `npm run generate:api` — _outcome: `test_openapi_snapshot.py` pasa y `src/api/generated/matriz.ts` exporta `useListAccounts`, `useListInstruments`, `useListOrders`, `useCreateOrder`, `useCancelOrder` (EB-34, UB-5)_

### Wave 5 (depends on T2, T7)

- [x] T8: Implementar `frontend/src/pages/orders/OrdersTable.tsx` (columnas, `—`, `Tag` de estado, «Cancelar» con `Popconfirm`) y `OrdersTable.test.tsx` — _outcome: los tests verifican columnas, cancelabilidad por estado y que descartar no dispara `onCancel` (EB-2, EB-3, EB-11, EB-12, EB-13, EB-17)_
- [x] T9: Implementar `frontend/src/pages/orders/NewOrderModal.tsx` y `NewOrderModal.test.tsx` — _outcome: los tests verifican validación, Market vs Limit, selects sin texto libre, estados de instrumentos, loading anti-doble-envío, error que conserva valores, éxito que resetea y Escape que cierra sin `POST` (EB-18…EB-33)_

### Wave 6 (depends on T8, T9)

- [x] T10: Reescribir `frontend/src/pages/OrdersPage.tsx` (título conservado, selector de cuenta, «Actualizar», «Nueva orden», polling condicional, override `PENDING_CANCEL`) y crear `OrdersPage.test.tsx` con router en memoria — _outcome: `npm test` pasa cubriendo carga, vacío, sin cuentas, error, error con datos previos, polling que arranca/se detiene/se reanuda, cancelación (éxito, error, descartada) y alta exitosa que refresca, con `AppLayout.test.tsx` sin cambios (EB-1, EB-4, EB-5, EB-7, EB-8, EB-9, EB-10, EB-14, EB-15, EB-16, EB-21, EB-33, UB-1, UB-2, UB-3, UB-10, UB-11)_

### Wave 7 (depends on T4, T10)

- [x] T11: Actualizar `CLAUDE.md:7,23`, `worker/CLAUDE.md:5,30`, `backend/CLAUDE.md`, `frontend/CLAUDE.md` (tabla `data-testid`), crear `broker/CLAUDE.md` y ajustar `README.md:9,21` — _outcome: la documentación nombra `broker/src/broker/matriz_gateway.py` como único acceso a Matriz y lista los endpoints, `MATRIZ_ACCOUNTS` y los `data-testid` nuevos (EB-37, EB-38)_
- [x] T12: Correr `scripts/check.sh` y `docker compose up --build` — _outcome: «Todos los gates pasaron» y `/health` responde 200 con el stack levantado (UB-4, UB-6, UB-8, EB-39)_
