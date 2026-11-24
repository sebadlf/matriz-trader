# Tasks — Quiero que obtengas la market data de todos

### Wave 1
- [x] T1 @backend-expert: Agregar `MarketDecimal` y `Percent` a `app/domain/numeric.py`, `MarketDataUnavailableError` a `app/domain/errors.py` y crear `app/domain/market_data.py` (`to_decimal`, `epoch_ms_to_utc`, `epoch_s_to_utc`, `spread_pct`) con `tests/test_market_data_domain.py` (Hypothesis) — _outcome: `uv run pytest tests/test_market_data_domain.py` pasa cubriendo conversión vía `str`, `None`/NaN, UTC, fórmula, redondeo `ROUND_HALF_EVEN`, `null` con precios <= 0 y negativo con libro cruzado (AC-3, AC-4, AC-5, AC-8, AC-9, AC-10)_
- [x] T2 @frontend-expert: Agregar `formatPercent` y `formatTime` a `src/utils/format.ts`, crear `src/constants/marketData.ts` (`MARKET_DATA_POLL_INTERVAL_MS`, `EMPTY_CELL`) y extender `format.test.ts` — _outcome: `vp test run src/utils/format.test.ts` pasa con `formatPercent("0.1250") === "0,12%"` sin convertir a `number` (AC-12, AC-24)_

### Wave 2 (depends on T1)
- [x] T3 @backend-expert: Crear `app/schemas/market_data.py` (`MarketDataRow`, `MarketDataResponse`) y `app/services/market_data.py` (`MarketDataSource`, `open_market_data_client`, `fetch_all_snapshots`, `snapshot_to_row`, `list_market_data` con manejo de errores y log) — _outcome: tests de servicio con fuente fake prueban paginación completa, mapeo de cada campo, filas sin datos y `MarketDataUnavailableError` con log sin secretos (AC-1, AC-2, AC-5, AC-6, AC-20, AC-21)_

### Wave 3 (depends on T3)
- [x] T4 @backend-expert: Agregar `get_market_data_source`/`MarketDataSourceDep` en `app/api/deps.py`, `UPSTREAM_PROBLEM_RESPONSE` en `app/api/errors.py`, la ruta `app/api/routes/market_data.py` registrada en `app/api/router.py`, el override en `tests/test_contract.py`, `tests/test_market_data.py`, y regenerar `backend/openapi.json` — _outcome: `scripts/gate.sh backend full` pasa; `GET /api/market-data` responde 200 con filas y 502 `problem+json` con `correlation_id` ante fallos; `openapi.json` publica `listMarketData` con tag `market-data` (AC-1, AC-2, AC-7, AC-20, AC-21)_

### Wave 4 (depends on T2, T4)
- [x] T5 @frontend-expert: Regenerar el cliente Orval y crear `filterRows.ts`, `useMarketDataFilters.ts` y `MarketDataFilters.tsx` en `src/screens/MarketDataScreen/` con sus tests — _outcome: tests de filtros pasan: símbolo sin distinguir mayúsculas, mercados presentes en los datos, AND entre ambos y sincronía con los query params (AC-15, AC-16, AC-17, AC-18)_

### Wave 5 (depends on T5)
- [x] T6 @frontend-expert: Crear `MarketDataTable.tsx`, `MarketDataScreen.tsx`, `index.ts`, la ruta en `src/constants/routes.ts` y `src/app/routes.tsx`, y sus tests con MSW — _outcome: `scripts/gate.sh frontend full` pasa; `/market-data` muestra la tabla con las 19 columnas, spinner, vacío, filtros sin coincidencias con "Limpiar filtros", error con "Reintentar", polling cada 5 s, última actualización y aviso que conserva los datos ante un refetch fallido (AC-9, AC-11, AC-12, AC-13, AC-14, AC-19, AC-22, AC-23, AC-24, AC-25, AC-26)_

### Wave 6 (depends on T6)
- [x] T7 @frontend-expert: Agregar `e2e/market-data.spec.ts` (500 filas mockeadas, filtro desde la URL, "Limpiar filtros") y el caso axe de `/market-data` en `e2e/a11y.spec.ts` — _outcome: `scripts/gate.sh e2e` pasa con 500 filas renderizadas y sin violaciones WCAG 2.2 AA (AC-11, AC-15, AC-18, AC-19)_
