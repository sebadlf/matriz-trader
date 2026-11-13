# Tasks — Quiero que crees un layout simple en el

### Wave 1

- [x] T1: Crear `frontend/src/pages/OrdersPage.tsx` con título «Órdenes» y `data-testid="page-ordenes"`, sin imports de API — _outcome: el componente `OrdersPage` existe y compila con `npm run typecheck` (AC-15, AC-17)_
- [x] T2: Crear `frontend/src/pages/StrategiesPage.tsx` con título «Estrategias» y `data-testid="page-estrategias"`, sin imports de API — _outcome: el componente `StrategiesPage` existe y compila con `npm run typecheck` (AC-16, AC-17)_
- [x] T3: Quitar de `HealthPage` (`frontend/src/pages/HealthPage.tsx:58-67`) el `Layout` propio y el título «Matriz Trader», reemplazándolo por el título «Estado» — _outcome: `npm test -- HealthPage` sigue pasando sin cambios en el test (AC-18)_
- [x] T4: Crear `frontend/src/layout/AppLayout.tsx` con `Sider` (logo `app-logo` como `<Link to="/orders">`, `Menu` `app-menu` inline con 3 ítems `<Link>` y `selectedKeys` desde `useLocation`) y `Content` con `<Outlet />` — _outcome: `AppLayout` compila y pasa `npm run lint` (AC-1, AC-2, AC-3, AC-4, AC-5, AC-8, AC-9, AC-10)_
- [x] T5: Cambiar `e2e/tests/test_health_page.py:5` a `page.goto(base_url + "/health")` — _outcome: el test de salud apunta a `/health` y pasa `uv run ruff check e2e` (AC-19)_

### Wave 2 (depends on T1, T2, T3, T4)

- [x] T6: Crear `frontend/src/routes.tsx` (ruta layout + `orders`, `strategies`, `health`, `index`/`*` → `<Navigate to="/orders" replace />`) y reescribir `frontend/src/router.tsx` para usar `createBrowserRouter(routes)` — _outcome: `npm run build` termina OK y en `npm run dev` abrir `/` lleva a `/orders` dentro del layout (AC-1, AC-6, AC-7, AC-11, AC-12, AC-18)_

### Wave 3 (depends on T6)

- [x] T7: Escribir `frontend/src/layout/AppLayout.test.tsx` con los 8 casos de «Key implementation details» usando `createMemoryRouter(routes, …)` — _outcome: `npm test` en `frontend/` pasa incluyendo los nuevos tests (AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12, AC-13, AC-15, AC-16, AC-17, AC-18, AC-20)_
- [x] T8: Crear `e2e/tests/test_navigation.py` con `test_root_redirects_and_menu_navigates_without_reload` y `test_direct_load_of_strategies` — _outcome: el archivo pasa `uv run ruff check e2e` y `uv run pyright` (AC-14, AC-21, NFR-1)_
- [x] T9: Actualizar `frontend/CLAUDE.md:9` (rutas, `AppLayout`, tabla de `data-testid`) y `e2e/CLAUDE.md:3-6` (`/health`, `test_navigation.py`) — _outcome: ambos `CLAUDE.md` documentan las rutas `/orders`, `/strategies`, `/health` y los `data-testid` nuevos (NFR-2, NFR-5)_

### Wave 4 (depends on T7, T8, T9)

- [x] T10: Correr `scripts/check.sh` y, con `docker compose up --build -d`, `uv run pytest e2e` — _outcome: `scripts/check.sh` sale con exit 0 y la suite e2e pasa completa (AC-14, AC-19, AC-21, NFR-4)_
