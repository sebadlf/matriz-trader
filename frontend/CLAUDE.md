# CLAUDE.md — frontend

SPA Vite + React 19 + TypeScript strict, React Router 8 (modo data), Ant Design 6, `@tanstack/react-query` con cliente generado por Orval 8. Proyecto npm aislado (no está en el workspace `uv`). Node 24 (`.nvmrc`).

## Archivos clave

- `openapi.json` — contrato versionado, exportado del backend. No editar ni formatear a mano (Biome lo excluye).
- `orval.config.ts` — genera `src/api/generated/` (ignorado por git) con el mutator `src/api/http.ts` (`customFetch`, `ApiError`, timeout 5 s).
- `src/routes.tsx` — tabla de rutas única (`RouteObject[]`), compartida por `src/router.tsx` (`createBrowserRouter`) y los tests (`createMemoryRouter`). Ruta layout sin `path` (`AppLayout`) con hijas `/orders` (`OrdersPage`), `/strategies` (`StrategiesPage`) y `/health` (`HealthPage`); `/` y cualquier ruta desconocida → `<Navigate to="/orders" replace />`.
- `src/layout/AppLayout.tsx` — `Layout` de antd: `Sider` con el logo «Matriz Trader» (`<Link to="/orders">`) y un `Menu` inline con tres ítems `<Link>` (Órdenes, Estrategias, Estado); `selectedKeys` se deriva de `useLocation().pathname`; el contenido va en `<Outlet />`. Las páginas no deben envolverse en otro `Layout`.
- `src/pages/` — `OrdersPage` (`/orders`: selector de cuenta, tabla con polling cada 5 s mientras haya órdenes no finales, cancelación con `Popconfirm` y modal de alta), `StrategiesPage` (cáscara, sin llamadas a la API) y `HealthPage` (`/health`, estado del backend y la BD).
- `src/pages/orders/` — `orderStatus.ts` (única clasificación final/no final y cancelabilidad), `format.ts` (`—` para vacíos, `describeApiError`), `OrdersTable.tsx` y `NewOrderModal.tsx`.

### Contrato de `data-testid` (tests unitarios y `e2e`)

| `data-testid`                                                                                                                 | Elemento                                                                                                 | Archivo                              |
| ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| `app-logo`                                                                                                                    | `<Link to="/orders">` «Matriz Trader»                                                                    | `src/layout/AppLayout.tsx`           |
| `app-menu`                                                                                                                    | `Menu` lateral                                                                                           | `src/layout/AppLayout.tsx`           |
| `menu-orders` / `menu-strategies` / `menu-health`                                                                             | `<Link>` de cada ítem del menú                                                                           | `src/layout/AppLayout.tsx`           |
| `page-ordenes`                                                                                                                | título «Órdenes»                                                                                         | `src/pages/OrdersPage.tsx`           |
| `orders-account-select`, `orders-refresh`, `orders-new`                                                                       | selector de cuenta, «Actualizar», «Nueva orden»                                                          | `src/pages/OrdersPage.tsx`           |
| `orders-loading`, `orders-error`, `orders-no-accounts`, `orders-action-error`                                                 | carga, error del listado (con «Reintentar»), sin cuentas (`MATRIZ_ACCOUNTS` vacío), error de cancelación | `src/pages/OrdersPage.tsx`           |
| `orders-table`, `orders-empty`                                                                                                | `Table` de órdenes y estado vacío «No hay órdenes»                                                       | `src/pages/orders/OrdersTable.tsx`   |
| `order-cancel-<cl_ord_id>`                                                                                                    | botón «Cancelar» de la fila                                                                              | `src/pages/orders/OrdersTable.tsx`   |
| `new-order-modal`, `new-order-error`, `new-order-submit`                                                                      | modal de alta, error de la API, «Enviar orden»                                                           | `src/pages/orders/NewOrderModal.tsx` |
| `new-order-account` / `new-order-instrument` / `new-order-side` / `new-order-type` / `new-order-price` / `new-order-quantity` | campos del modal                                                                                         | `src/pages/orders/NewOrderModal.tsx` |
| `page-estrategias`                                                                                                            | título «Estrategias»                                                                                     | `src/pages/StrategiesPage.tsx`       |
| `health-loading`, `health-status`, `health-database`, `health-error`                                                          | estados de `HealthPage`                                                                                  | `src/pages/HealthPage.tsx`           |
- `vite.config.ts` — `envDir: '..'` (lee el `.env` raíz), puerto `FRONTEND_DEV_PORT`, config de Vitest.
- `nginx.conf` + `Dockerfile` — producción: build estático con `VITE_API_BASE_URL=/api` y proxy `/api/` → backend.

## Comandos (desde `frontend/`)

```bash
npm ci --include=dev          # --include=dev por si NODE_ENV=production está en el shell
npm run dev                   # http://localhost:5173 (HMR); regenera el cliente Orval antes
npm run build                 # tsc -b && vite build; no necesita el backend en ejecución
npm run lint                  # biome lint + eslint (solo reglas react-hooks / react-refresh)
npm run format                # biome format --write
npm run format:check
npm run typecheck
npm test                      # vitest run (jsdom)
npm run generate:api          # regenerar el cliente a mano
```

Si cambia la API: desde la raíz `uv run python -m backend.export_openapi` y commitear `openapi.json`.
