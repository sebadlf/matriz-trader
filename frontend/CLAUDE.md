# CLAUDE.md — frontend

Convenciones del frontend de `matriz-trader`. El contexto general, la Definición de terminado y la checklist están en el [`CLAUDE.md` de la raíz](../CLAUDE.md). Cuando una regla la hace cumplir una herramienta, la línea termina con «— lo verifica `<herramienta>`».

## 1. Comandos (desde `frontend/`)

```bash
vp install                 # instala dependencias (pnpm, lockfile congelado en Docker y CI)
vp dev                     # servidor de desarrollo en :5173 (proxy de /api al backend)
vp build                   # build de producción en dist/
vp check                   # formato + lint + type-check de src/ (gate principal)
vp check --fix             # lo mismo, corrigiendo formato y lint automáticos
vp run typecheck:node      # type-check de vite.config.ts y playwright.config.ts
vp run lint:arch           # reglas de dependencia entre carpetas (dependency-cruiser)
vp run lint:unused         # archivos, exports y dependencias sin usar (knip)
vp test run                # tests unitarios (Vitest), una pasada
vp test run --coverage     # con cobertura (umbral 70 %)
vp run size                # presupuesto del bundle (después de vp build)
vp run generate:api        # regenera el cliente Orval
vp run e2e                 # Playwright, incluida accesibilidad
```

Para correr todo junto usá `scripts/gate.sh frontend` y `scripts/gate.sh e2e` desde la raíz.

- Usá siempre `vp`. No invoques `vitest`, `oxlint`, `oxfmt` ni `vite` directamente.
- Los comandos integrados (`dev`, `build`, `test`, `lint`, `fmt`, `check`) tienen prioridad sobre los scripts de `package.json` con el mismo nombre. Para correr scripts propios usá `vp run <script>`.
- La configuración de lint, formato y tests vive en `vite.config.ts`. No crees archivos de configuración paralelos (`.oxlintrc`, `vitest.config.ts`, etc.). Las únicas excepciones son las de herramientas que `vp` no cubre: `.dependency-cruiser.cjs`, `knip.config.ts` y `playwright.config.ts`.
- No exportes `NODE_ENV=production` en la shell al correr `vp test`: Vitest carga el build de producción de React y los tests fallan con `React.act is not a function` (`scripts/gate.sh` hace `unset NODE_ENV`).

## 2. Estructura

```
frontend/
├── src/
│   ├── app/                 # arranque: providers, router, theme de AntD
│   │   ├── providers.tsx    # ConfigProvider + App de AntD + QueryClientProvider
│   │   ├── routes.tsx       # árbol de rutas (lazy) y ruta 404
│   │   ├── router.tsx       # AppRouter (createBrowserRouter)
│   │   └── theme.ts
│   ├── api/
│   │   ├── generated/       # SALIDA DE ORVAL (cliente, modelos y handlers *.msw.ts) — nunca editar a mano
│   │   ├── mutator.ts       # único punto con fetch (baseURL, errores, en el futuro auth)
│   │   └── queryClient.ts
│   ├── screens/             # una carpeta por pantalla/ruta
│   │   └── <NombreScreen>/
│   │       ├── <NombreScreen>.tsx
│   │       ├── components/  # componentes usados solo por esta pantalla
│   │       ├── hooks/       # hooks usados solo por esta pantalla
│   │       ├── <NombreScreen>.test.tsx
│   │       └── index.ts     # API pública de la pantalla
│   ├── components/          # componentes compartidos y reutilizables (sin lógica de negocio)
│   ├── layouts/             # layouts de rutas (RootLayout)
│   ├── hooks/               # hooks compartidos
│   ├── stores/              # stores de Zustand
│   ├── utils/               # funciones puras, sin React (format.ts)
│   ├── constants/           # rutas (routes.ts), claves, valores fijos
│   ├── types/               # tipos de dominio compartidos que no vienen de la API
│   └── test/                # setup.ts, server.ts (MSW) y render.tsx (renderWithProviders)
├── e2e/                     # tests de Playwright (home.spec.ts, a11y.spec.ts)
├── .dependency-cruiser.cjs  # reglas de dependencia entre carpetas
├── knip.config.ts           # código y dependencias sin usar
├── orval.config.ts
├── playwright.config.ts
└── vite.config.ts           # única config de Vite, lint, formato y tests
```

Los directorios vacíos (`components/`, `hooks/`, `stores/`, `utils/`, `types/`) llevan un `.gitkeep`.

## 3. Reglas de dependencia (quién puede importar a quién)

- `app/` → puede importar todo.
- `screens/` → `components`, `layouts`, `hooks`, `stores`, `api`, `utils`, `constants`, `types`.
- **Una pantalla nunca importa de otra pantalla.** Si dos pantallas necesitan lo mismo, subilo a `components/` o `hooks/` — lo verifica `vp run lint:arch` (`screen-no-otra-screen`).
- `components/` no importa de `screens/`, `api/`, `stores/` ni `layouts/` — lo verifica `vp run lint:arch` (`components-limites`).
- `hooks/` no importa de `screens/`, `components/` ni `layouts/` — lo verifica `vp run lint:arch` (`hooks-limites`).
- `utils/` y `constants/` solo importan de `types/` (y entre sí): sin React ni paquetes npm — lo verifica `vp run lint:arch` (`utils-constants-puros`).
- Prohibidas las dependencias circulares — lo verifican `vp run lint:arch` (`no-circular`) y Oxlint (`import/no-cycle`).
- Fuera de `app/` y de la propia pantalla, se importa una pantalla solo a través de su `index.ts` — lo verifica `vp run lint:arch` (`screen-via-index`).
- Usá el alias `@/` para `src/`. Nada de imports relativos que suban más de un nivel (`../../`) — lo verifica Oxlint (`no-restricted-imports`).
- Sin código, exports ni dependencias sin usar — lo verifica `vp run lint:unused` (knip). Si knip marca un falso positivo, se agrega a `ignoreDependencies` de `knip.config.ts` con un comentario; nunca código propio.

## 4. Acceso al backend: solo vía Orval

- **El frontend solo habla con el backend mediante el cliente generado por Orval.** `fetch` aparece únicamente en `src/api/mutator.ts`, y no se usa `axios` — lo verifica Oxlint (`no-restricted-globals`, `no-restricted-properties` y `no-restricted-imports`).
- **`src/api/generated/` es código generado y no se edita a mano** — lo verifica el hook `PreToolUse` de Claude Code. Está excluido de lint y formato. Si algo está mal, se corrige el contrato del backend o `orval.config.ts`, y se regenera.
- `orval.config.ts` usa `client: 'react-query'`, `httpClient: 'fetch'`, `mode: 'tags-split'`, `mock: true` (genera los handlers de MSW) y el mutator `customFetch` de `src/api/mutator.ts`. El input es el archivo versionado `../backend/openapi.json`, así que generar no requiere el backend en ejecución.
- El mutator es el único lugar con baseURL, headers de auth, manejo de 401/403 y normalización de errores. Cuando la respuesta no es `ok` lanza `ApiError`, con `status`, `body` y, si el cuerpo es `ProblemDetails` (RFC 9457), `title`, `detail` y `correlationId` — lo verifica `src/api/mutator.test.ts`. Mostrá el `correlationId` en los errores que el usuario pueda reportar.
- Usá los tipos generados por Orval; no los redefinas a mano. Si necesitás un tipo de dominio, derivalo (`Pick`, `Omit`, mapeos).
- Para transformar o combinar datos de la API, envolvé el hook generado en un hook propio (`screens/X/hooks/useX.ts` o `hooks/`) y usá `select` de react-query.
- Después de una mutación, invalidá las queries afectadas con las query keys generadas (`getXQueryKey()`). No escribas keys como strings.
- Toda pantalla que consume datos maneja explícitamente los estados de carga, error y vacío (`Spin`/`Skeleton`, `Alert`/`Result`, `Empty` de AntD).

### Flujo para cambiar el contrato

1. Cambiá o agregá los endpoints en `backend/app/api/routes/` (con `operation_id` explícito; ver `backend/CLAUDE.md`).
2. Exportá el esquema: `cd backend && uv run python -m app.scripts.export_openapi`.
3. Regenerá el cliente: `cd frontend && vp run generate:api`, y corré `vp check` para que los cambios de contrato aparezcan como errores de tipo.
4. Commiteá juntos `backend/openapi.json` y `frontend/src/api/generated/` — lo verifica `scripts/hooks/check-generated-sync.sh` (lefthook).

Un export olvidado rompe `uv run pytest` (`backend/tests/test_openapi_export.py`).

## 5. Estado

| Tipo de estado                                                      | Dónde vive                                              |
| ------------------------------------------------------------------- | ------------------------------------------------------- |
| Datos del servidor                                                  | react-query (vía Orval). **Nunca** se copian a Zustand. |
| Estado de la URL (filtros, paginación, tab activa, id seleccionado) | Parámetros de ruta / search params de React Router      |
| Estado de formulario                                                | `Form` de Ant Design                                    |
| Estado local de un componente                                       | `useState` / `useReducer`                               |
| Estado global de cliente (sesión, preferencias, UI compartida)      | Zustand                                                 |

- Un store de Zustand por dominio (`stores/useSessionStore.ts`), pequeño y tipado. Leé con selectores (`useStore((s) => s.campo)`) o `useShallow`; las acciones viven dentro del store; exportá un reset para los tests. `persist` solo con una razón explícita y con `version`/`migrate`.
- Al crear el primer store, quitá `zustand` de `ignoreDependencies` en `knip.config.ts`.

## 6. Navegación

- Las rutas se definen en `src/app/routes.tsx` (montadas por `src/app/router.tsx`) y sus paths en `src/constants/routes.ts` (`ROUTES`). No escribas paths como strings sueltos.
- Las pantallas se cargan con `lazy`. Cada ruta tiene `errorElement`; la ruta `*` muestra `NotFoundScreen`.
- Navegá con `<Link>` / `useNavigate`, nunca con `window.location`.

## 7. Ant Design y UI

- El tema se configura en `src/app/theme.ts` vía `ConfigProvider`. No hardcodees colores, espaciados ni tipografías. Los tokens de color ya están ajustados para cumplir contraste WCAG AA; si cambiás uno, corré `scripts/gate.sh e2e`.
- Usá `App.useApp()` para `message`, `notification` y `modal`, no las APIs estáticas.
- Preferí los componentes de layout de AntD (`Flex`, `Space`, `Row`/`Col`, `Layout`) a CSS propio.
- Formularios con `Form.useForm<T>()` y `rules`; tablas con `rowKey` y `columns` tipadas con `ColumnsType<T>`.
- Accesibilidad: todo control tiene label, los botones de solo icono llevan `aria-label` y no se usan `div` clickeables en lugar de `Button` — lo verifican Oxlint (`jsx-a11y`) y axe en `e2e/a11y.spec.ts` (WCAG 2.2 AA).
- Los números se muestran con `formatPrice` y `formatQuantity` de `src/utils/format.ts` (`Intl.NumberFormat` con locale `es-AR`, instancias reutilizadas y redondeo `halfEven`, igual que el backend). No uses `toFixed`, `toLocaleString` ni `Number(...)` para formatear.

## 8. TypeScript

- `strict`, `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, `noImplicitReturns`, `verbatimModuleSyntax`, `noUnusedLocals`, `noUnusedParameters` y `noFallthroughCasesInSwitch` están activos en `tsconfig.json` y `tsconfig.node.json`; `tsconfig.json` (el de `src/`) suma `noUncheckedIndexedAccess` y `noImplicitOverride` — lo verifican `vp check` y `vp run typecheck:node`.
- Sin `enum` ni parameter properties: usá uniones de literales u objetos `as const` — lo verifica TypeScript (`erasableSyntaxOnly`, TS1294).
- Prohibido `any`: usá `unknown` y estrechá con guards — lo verifica Oxlint (`typescript/no-explicit-any`).
- Sin `!` — lo verifica Oxlint (`typescript/no-non-null-assertion`). Sin `as` para silenciar errores: preferí un type guard — lo verifica Oxlint (`typescript/no-unsafe-type-assertion`); si es inevitable, deshabilitá la regla en esa línea con un comentario que lo justifique.
- Sin `@ts-ignore`; `@ts-expect-error` solo con descripción — lo verifica Oxlint (`typescript/ban-ts-comment`).
- Toda promesa se espera o se maneja — lo verifica Oxlint (`typescript/no-floating-promises`).
- Las props se declaran como `type <Componente>Props = {...}`.

## 9. Componentes y hooks

- Un componente por archivo, en `PascalCase`. Los hooks se llaman `useAlgo` y viven en `useAlgo.ts`. Un archivo de componente solo exporta componentes — lo verifica Oxlint (`react/only-export-components`).
- Hooks según las reglas de React y con dependencias completas — lo verifica Oxlint (`react/rules-of-hooks`, `react/exhaustive-deps`).
- La pantalla obtiene datos y orquesta, los hooks contienen la lógica y los componentes presentan. Los componentes de `components/` reciben datos por props y no llaman a la API.
- No uses `useEffect` para derivar estado ni para sincronizar datos del servidor. `useMemo`/`useCallback` solo con un motivo concreto.
- Si un archivo supera ~200 líneas o mezcla datos, lógica y presentación, dividilo.

## 10. Errores, seguridad y rendimiento

- Ningún error se traga en silencio: se muestra al usuario o se reporta.
- Sin secretos en el código. Solo las variables con prefijo `VITE_` llegan al bundle (y son públicas); las demás del `.env` las usa solo `vite.config.ts`.
- Sin `dangerouslySetInnerHTML` — lo verifica Oxlint (`react/no-danger`). Sin `console.log` — lo verifica Oxlint (`no-console`).
- El JavaScript del build, comprimido con gzip, no supera el presupuesto de `size-limit` en `package.json` — lo verifica `vp run size`. Subir el límite exige justificarlo en el PR.

## 11. Tests

### Unitarios (`vp test`)

- Junto al código: `Algo.test.tsx` al lado de `Algo.tsx`. Importá `describe`, `it`, `expect`, `vi` y compañía de `vite-plus/test` — lo verifica Oxlint (`vite-plus/prefer-vite-plus-imports`).
- Renderizá con `renderWithProviders()` de `src/test/render.tsx`: monta los providers de la app, un `QueryClient` nuevo con `retry: false` y un router en memoria (`route`, y opcionalmente `routes` para probar el árbol real de `app/routes.tsx`). Devuelve también `user` (`userEvent`).
- Testeá comportamiento visible. Buscá por accesibilidad: `getByRole` > `getByLabelText` > `getByText`; `getByTestId` solo como último recurso. Usá `userEvent` y `findBy*` / `waitFor` para lo asíncrono.
- **La red se mockea en el borde con MSW 2**, no en los hooks generados, así se ejercita el mutator real. `src/test/setup.ts` levanta el `server` de `src/test/server.ts` con `onUnhandledRequest: "error"`: un request sin handler hace fallar el test. Registrá handlers por test con `server.use(...)`, usando los generados por Orval (`getGetHealthMockHandler({...})` de `generated/<tag>/<tag>.msw.ts`) o `http.get("*/api/...", ...)` para errores y casos especiales. No uses `vi.stubGlobal("fetch", ...)`.
- La cobertura de líneas, branches, funciones y sentencias no baja del 70 % (sin contar `src/api/generated/`, `src/test/` ni los tests) — lo verifica `vp test run --coverage`.
- Reseteá los stores de Zustand entre tests.

### E2E (Playwright)

- Viven en `e2e/`. `playwright.config.ts` levanta `vp dev` en :5173. Con `CI` definido usa `forbidOnly`, 2 reintentos y trace en el primer reintento; CI publica los traces cuando un test falla.
- Los e2e mockean `/api/health` con `page.route`, así que no dependen del backend ni de PostgreSQL.
- Cada pantalla nueva se agrega a `e2e/a11y.spec.ts`, que exige cero violaciones de axe con `wcag2a`, `wcag2aa`, `wcag21aa` y `wcag22aa` — lo verifica `scripts/gate.sh e2e`.
- Usá locators por rol y texto, nunca selectores CSS frágiles ni `waitForTimeout`. Cada test es independiente.
- Todo bug corregido incluye un test que lo reproduce.

## 12. Reglas de UI para órdenes

Hoy ninguna pantalla envía órdenes. La primera que lo haga tiene que cumplir todo lo siguiente:

1. **Confirmación explícita.** Todo envío de orden pide confirmación con `modal.confirm` de `App.useApp()`, mostrando lado (compra/venta), cantidad, precio y notional. La orden se envía solo desde el `onOk` del modal.
2. **Sin doble envío.** Mientras la mutación está pendiente, el botón de envío queda `loading` y `disabled` (derivado de `isPending` de la mutación, no de un `useState` paralelo).
3. **Precios y cantidades como string.** Viajan como string decimal, igual que los tipos `Price`/`Quantity` del backend, y nunca se convierten a `number` para calcular o enviar. Si hace falta aritmética, se hace en el backend.
4. **Formato único.** Precios, cantidades y notional se muestran con los formatters de `src/utils/format.ts`.
