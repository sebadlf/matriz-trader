# CLAUDE.md — matriz-trader

Guía para agentes de IA y desarrolladores que trabajan en este repo. Si una regla te impide resolver la tarea, detenete y explicá el conflicto antes de romperla. La instalación y el uso están en [`README.md`](README.md).

## 1. Contexto

- Monorepo con dos módulos: `backend/` (Python 3.13 + FastAPI) y `frontend/` (React + TypeScript + Vite+).
- Hoy es solo un esqueleto: el único endpoint es `GET /api/health` y el frontend tiene una pantalla de inicio y una 404. No hay lógica de negocio.
- Las librerías internas `market-data-client` (tag `market-data-client-v0.7.1`) y `matriz-client` (tag `matriz-client-v0.4.0`) de `gravity-quant/market-libs` se instalan por SSH (`backend/pyproject.toml`, `[tool.uv.sources]`).
- **Un único `.env`, en la raíz.** Lo leen el backend (`ROOT_ENV_FILE` en `backend/app/core/config.py`), el frontend (`envDir` en `frontend/vite.config.ts`) y Docker Compose. No crees `backend/.env` ni `frontend/.env`. Toda variable nueva se agrega a `.env.example` con un valor de ejemplo no secreto y un comentario.
- Los comandos de cada módulo se ejecutan desde su carpeta (`backend/` o `frontend/`).

## 2. Stack por módulo

### Backend (`backend/`)

| Área | Herramienta |
|---|---|
| Lenguaje | Python 3.13 (`backend/.python-version`) |
| Gestor de proyecto | uv (`pyproject.toml` + `uv.lock` versionado; `package = false`) |
| API | FastAPI + uvicorn |
| Configuración | pydantic-settings (`Settings` tipado) |
| Base de datos | PostgreSQL 17 + SQLAlchemy 2.0 async + psycopg 3 |
| Lint y formato | Ruff (incluye las reglas `ANN`) |
| Tipado | mypy `strict` con el plugin `pydantic.mypy` |
| Tests | pytest + pytest-asyncio + `httpx.AsyncClient` |

Toda la configuración de Ruff, mypy y pytest vive en `backend/pyproject.toml`.

### Frontend (`frontend/`)

| Área | Herramienta |
|---|---|
| Lenguaje | TypeScript en modo `strict` |
| UI | React 19 + Ant Design 6 |
| Toolchain | Vite+ (CLI `vp`: Vite, Vitest, Oxlint, Oxfmt) |
| Gestor de paquetes | pnpm (`packageManager` en `package.json`, `pnpm-lock.yaml` versionado) |
| Acceso al backend | Orval 8, cliente `react-query` (TanStack Query) |
| Navegación | React Router 7 |
| Estado de cliente | Zustand |
| Tests unitarios | `vp test` (Vitest) + React Testing Library |
| Tests e2e | Playwright |

No agregues librerías que dupliquen una responsabilidad de esta tabla (otro cliente HTTP, otro gestor de estado, otra librería de componentes, ESLint, Prettier, Jest, etc.). Si necesitás una dependencia nueva, justificá por qué antes de instalarla.

## 3. Estructura de carpetas

### `backend/`

```
backend/
├── app/
│   ├── __init__.py          # __version__
│   ├── __main__.py          # entrypoint: python -m app [--reload]
│   ├── main.py              # create_app(), lifespan, app
│   ├── core/config.py       # Settings, load_settings(), get_settings()
│   ├── db/
│   │   ├── base.py          # Base (DeclarativeBase + naming convention), TimestampMixin
│   │   └── session.py       # build_engine(), build_session_factory(), get_session()
│   ├── api/
│   │   ├── router.py        # api_router con prefijo /api
│   │   └── routes/          # un módulo por grupo de endpoints (health.py)
│   ├── schemas/             # modelos Pydantic de request/response
│   └── scripts/
│       └── export_openapi.py  # escribe backend/openapi.json
├── tests/                   # pytest (conftest.py con los fixtures test_env y client)
├── openapi.json             # GENERADO y versionado: input de Orval
├── pyproject.toml
└── uv.lock
```

- `create_app()` no lee `Settings`: importar `app.main` (tests, export del OpenAPI) no requiere `.env` ni base de datos. La configuración y el engine se crean en el `lifespan`.
- Los endpoints nuevos van en `app/api/routes/<grupo>.py` y se registran en `app/api/router.py`. Los esquemas van en `app/schemas/`. Los modelos ORM heredan de `app.db.base.Base`.

### `frontend/`

```
frontend/
├── src/
│   ├── app/                 # arranque: providers, router, theme de AntD
│   │   ├── providers.tsx    # ConfigProvider + App de AntD + QueryClientProvider
│   │   ├── routes.tsx       # árbol de rutas (lazy) y ruta 404
│   │   ├── router.tsx       # AppRouter (createBrowserRouter)
│   │   └── theme.ts
│   ├── api/
│   │   ├── generated/       # SALIDA DE ORVAL — nunca editar a mano
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
│   ├── utils/               # funciones puras, sin React
│   ├── constants/           # rutas (routes.ts), claves, valores fijos
│   ├── types/               # tipos de dominio compartidos que no vienen de la API
│   └── test/                # setup.ts y render.tsx (renderWithProviders)
├── e2e/                     # tests de Playwright
├── orval.config.ts
├── playwright.config.ts
└── vite.config.ts           # única config de Vite, lint, formato y tests
```

Los directorios vacíos (`components/`, `hooks/`, `stores/`, `utils/`, `types/`) llevan un `.gitkeep`.

### Reglas de dependencia del frontend (quién puede importar a quién)

- `app/` → puede importar todo.
- `screens/` → `components`, `layouts`, `hooks`, `stores`, `api`, `utils`, `constants`, `types`.
- **Una pantalla nunca importa de otra pantalla.** Si dos pantallas necesitan lo mismo, subilo a `components/` o `hooks/`.
- `components/` → `hooks`, `utils`, `constants`, `types`. **Nunca** de `screens/` ni de `api/generated` directamente.
- `hooks/` → `api`, `stores`, `utils`, `constants`, `types`.
- `utils/` y `constants/` → no importan nada del proyecto salvo `types/`. Sin React.
- Prohibidas las dependencias circulares.
- Importá a través del `index.ts` de cada pantalla o módulo, no de sus archivos internos.
- Usá el alias `@/` para `src/`. No uses imports relativos que suban más de un nivel (`../../`).

## 4. Comandos

### Backend (desde `backend/`)

```bash
uv sync                                       # crea .venv e instala todo (requiere acceso SSH a market-libs)
uv run python -m app --reload                 # servidor de desarrollo en :8000
uv run ruff check .                           # lint (incluye ANN)
uv run ruff format --check .                  # formato (sin --check, formatea)
uv run mypy .                                 # tipado strict
uv run pytest                                 # tests
uv run python -m app.scripts.export_openapi   # regenera backend/openapi.json
```

`python -m app` valida la configuración antes de levantar uvicorn: si falta una variable obligatoria o es inválida, sale con código 1 y el mensaje `Configuración inválida: <VARIABLE>`.

### Frontend (desde `frontend/`)

```bash
vp install                 # instala dependencias (pnpm, lockfile congelado en Docker)
vp dev                     # servidor de desarrollo en :5173 (proxy de /api al backend)
vp build                   # build de producción en dist/
vp check                   # formato + lint + type-check (gate principal)
vp lint                    # solo Oxlint (con type-check)
vp fmt --check             # solo Oxfmt (sin --check, formatea)
vp test run                # tests unitarios (Vitest), una pasada
vp run generate:api        # regenera el cliente Orval (script de package.json)
vp run e2e                 # Playwright (script de package.json)
```

- Usá siempre `vp`. No invoques `vitest`, `oxlint`, `oxfmt` ni `vite` directamente.
- Los comandos integrados (`dev`, `build`, `test`, `lint`, `fmt`, `check`) tienen prioridad sobre los scripts de `package.json` con el mismo nombre. Para correr scripts propios usá `vp run <script>`.
- La configuración de lint, formato y tests vive en `frontend/vite.config.ts`. No crees archivos de configuración paralelos (`.oxlintrc`, `vitest.config.ts`, etc.).
- No exportes `NODE_ENV=production` en la shell al correr `vp test`: Vitest respeta ese valor, carga el build de producción de React y los tests fallan con `React.act is not a function`.

## 5. Acceso al backend: solo vía Orval

- **El frontend solo habla con el backend mediante el cliente generado por Orval.** `fetch` aparece únicamente en `src/api/mutator.ts`. Prohibido usar `fetch` o `axios` en componentes, hooks, stores o pantallas.
- **`src/api/generated/` es código generado y no se edita a mano.** Está excluido de lint y formato (`ignorePatterns` en `vite.config.ts`). Si algo está mal, se corrige el contrato del backend o `orval.config.ts`, y se regenera.
- `orval.config.ts` usa `client: 'react-query'`, `httpClient: 'fetch'`, `mode: 'tags-split'` y el mutator `customFetch` de `src/api/mutator.ts`. El input es el archivo versionado `../backend/openapi.json`, así que generar no requiere el backend en ejecución.
- El mutator es el único lugar con baseURL, headers de auth, manejo de 401/403 y normalización de errores. Lanza `ApiError` cuando la respuesta no es `ok`.
- Usá los tipos generados por Orval; no los redefinas a mano. Si necesitás un tipo de dominio, derivalo (`Pick`, `Omit`, mapeos).
- Para transformar o combinar datos de la API, envolvé el hook generado en un hook propio (`screens/X/hooks/useX.ts` o `hooks/`) y usá `select` de react-query.
- Después de una mutación, invalidá las queries afectadas con las query keys generadas (`getXQueryKey()`). No escribas keys como strings.
- Toda pantalla que consume datos maneja explícitamente los estados de carga, error y vacío (`Spin`/`Skeleton`, `Alert`/`Result`, `Empty` de AntD).

### Flujo para cambiar el contrato

1. Cambiá o agregá los endpoints en `backend/app/api/routes/` (con `operation_id` explícito).
2. Exportá el esquema: `cd backend && uv run python -m app.scripts.export_openapi`.
3. Regenerá el cliente: `cd frontend && vp run generate:api`, y corré `vp check` para que los cambios de contrato aparezcan como errores de tipo.
4. Commiteá juntos `backend/openapi.json` y `frontend/src/api/generated/`.

`backend/tests/test_openapi_export.py` falla si `openapi.json` no coincide con `create_app().openapi()`, así que un export olvidado rompe `uv run pytest`.

## 6. Convenciones del backend

- **Tipado completo.** Las reglas `ANN` de Ruff están habilitadas sin excepciones, ni siquiera en `tests/`: toda función anota parámetros y retorno.
- **mypy `strict = true`** con el plugin `pydantic.mypy` y **sin** el plugin de mypy de SQLAlchemy. Los modelos ORM se tipan con `Mapped[...]` y `mapped_column()`; nunca uses `Column(...)`.
- **`operation_id` explícito en cada ruta** (por ejemplo `operation_id="getHealth"`). De ahí salen los nombres estables que genera Orval (`getHealth`, `useGetHealth`, `getGetHealthQueryKey`).
- Cada ruta declara `response_model` con un esquema de `app/schemas/` y un `tags=[...]`, que define el archivo de salida de Orval (`generated/<tag>/<tag>.ts`).
- La configuración se lee solo a través de `Settings` (`get_settings()`); no uses `os.environ` directamente.
- Las sesiones de DB se obtienen con la dependencia `get_session`, que usa `app.state.session_factory` creado en el `lifespan`.
- Alembic todavía no está configurado: se agrega junto con el primer modelo de dominio.
- Tests: los endpoints se prueban con el fixture `client` (`httpx.AsyncClient` + `ASGITransport`, que no ejecuta el `lifespan`, así que no hace falta PostgreSQL). El fixture autouse `test_env` define un `DATABASE_URL` de prueba.

## 7. Convenciones del frontend

### Estado

| Tipo de estado | Dónde vive |
|---|---|
| Datos del servidor | react-query (vía Orval). **Nunca** se copian a Zustand. |
| Estado de la URL (filtros, paginación, tab activa, id seleccionado) | Parámetros de ruta / search params de React Router |
| Estado de formulario | `Form` de Ant Design |
| Estado local de un componente | `useState` / `useReducer` |
| Estado global de cliente (sesión, preferencias, UI compartida) | Zustand |

- Un store de Zustand por dominio (`stores/useSessionStore.ts`), pequeño y tipado. Leé con selectores (`useStore((s) => s.campo)`) o `useShallow`; las acciones viven dentro del store; exportá un reset para los tests. `persist` solo con una razón explícita y con `version`/`migrate`.

### Navegación

- Las rutas se definen en `src/app/routes.tsx` (montadas por `src/app/router.tsx`) y sus paths en `src/constants/routes.ts` (`ROUTES`). No escribas paths como strings sueltos.
- Las pantallas se cargan con `lazy`. Cada ruta tiene `errorElement`; la ruta `*` muestra `NotFoundScreen`.
- Navegá con `<Link>` / `useNavigate`, nunca con `window.location`.

### Ant Design y UI

- El tema se configura en `src/app/theme.ts` vía `ConfigProvider`. No hardcodees colores, espaciados ni tipografías.
- Usá `App.useApp()` para `message`, `notification` y `modal`, no las APIs estáticas.
- Preferí los componentes de layout de AntD (`Flex`, `Space`, `Row`/`Col`, `Layout`) a CSS propio.
- Formularios con `Form.useForm<T>()` y `rules`; tablas con `rowKey` y `columns` tipadas con `ColumnsType<T>`.
- Accesibilidad: todo control tiene label, los botones de solo icono llevan `aria-label` y no se usan `div` clickeables en lugar de `Button`.

### TypeScript

- `strict`, `noUncheckedIndexedAccess` y `noImplicitOverride` están activos, y `erasableSyntaxOnly` prohíbe `enum` y las parameter properties.
- Prohibido `any`: usá `unknown` y estrechá con guards. Sin `!` ni `as` para silenciar errores (si hacen falta, justificalos con un comentario). Sin `@ts-ignore`; `@ts-expect-error` solo con comentario.
- Usá uniones de literales u objetos `as const` en lugar de `enum`. Las props se declaran como `type <Componente>Props = {...}`.

### Componentes y hooks

- Un componente por archivo, en `PascalCase`. Los hooks se llaman `useAlgo` y viven en `useAlgo.ts`.
- La pantalla obtiene datos y orquesta, los hooks contienen la lógica y los componentes presentan. Los componentes de `components/` reciben datos por props y no llaman a la API.
- No uses `useEffect` para derivar estado ni para sincronizar datos del servidor. `useMemo`/`useCallback` solo con un motivo concreto.
- Si un archivo supera ~200 líneas o mezcla datos, lógica y presentación, dividilo.

### Errores, seguridad y rendimiento

- Ningún error se traga en silencio: se muestra al usuario o se reporta.
- Sin secretos en el código. Solo las variables con prefijo `VITE_` llegan al bundle (y son públicas); las demás del `.env` las usa solo `vite.config.ts`.
- Sin `dangerouslySetInnerHTML` con contenido que no controlás y sin `console.log` en el código final.

## 8. Tests

### Backend

- Los tests van en `backend/tests/test_<tema>.py`, todos anotados (regla `ANN`).
- `test_tooling.py` verifica que las libs de `market-libs` se importan y que la regla `ANN` sigue activa sin excepciones; no lo debilites.

### Frontend (unitarios, `vp test`)

- Junto al código: `Algo.test.tsx` al lado de `Algo.tsx`.
- Renderizá siempre con `renderWithProviders()` de `src/test/render.tsx`: monta los providers de la app, un `QueryClient` nuevo con `retry: false` y un router en memoria (`route`, y opcionalmente `routes` para probar el árbol real de `app/routes.tsx`). Devuelve también `user` (`userEvent`).
- Testeá comportamiento visible. Buscá por accesibilidad: `getByRole` > `getByLabelText` > `getByText`; `getByTestId` solo como último recurso. Usá `userEvent` y `findBy*` / `waitFor` para lo asíncrono.
- La red se mockea en el borde, no en los hooks generados: hoy `HomeScreen.test.tsx` usa `vi.stubGlobal("fetch", …)`, que además ejercita el mutator real.
- Reseteá los stores de Zustand entre tests.

### E2E (Playwright)

- Viven en `frontend/e2e/`. `playwright.config.ts` levanta `vp dev` en :5173.
- `e2e/home.spec.ts` mockea `/api/health` con `page.route`, así que no depende del backend ni de PostgreSQL.
- Usá locators por rol y texto, nunca selectores CSS frágiles ni `waitForTimeout`. Cada test es independiente.
- Todo bug corregido incluye un test que lo reproduce.

## 9. Definición de "terminado"

Un cambio está terminado solo si pasa todo lo que corresponde, en este orden, y viste la salida de cada comando.

**Backend** (desde `backend/`):

1. `uv run ruff check .` y `uv run ruff format --check .` sin errores.
2. `uv run mypy .` sin errores.
3. `uv run pytest` en verde.
4. Si cambió el contrato: `backend/openapi.json` regenerado (ver §5).

**Frontend** (desde `frontend/`):

1. `vp check` sin errores ni warnings nuevos.
2. `vp test run` en verde.
3. `vp build` compila.
4. `vp run e2e`, si el cambio toca un flujo cubierto por Playwright.
5. Si cambió el contrato del backend: el cliente Orval se regeneró y se commiteó junto con `openapi.json`.

Si algún comando falla y no podés arreglarlo, informá exactamente qué falló, con la salida.

## 10. Checklist de autorrevisión

- [ ] ¿Toda llamada al backend usa código generado por Orval? ¿Edité algo en `src/api/generated/`?
- [ ] ¿Respeté las reglas de dependencia entre carpetas? ¿Hay imports entre pantallas?
- [ ] ¿Cada estado está en el lugar correcto (servidor / URL / formulario / local / Zustand)?
- [ ] ¿Las pantallas manejan los estados de carga, error y vacío?
- [ ] ¿Hay `any`, `!`, `as` injustificados, `@ts-ignore` o `console.log`? ¿Hay funciones Python sin anotar?
- [ ] ¿Las rutas nuevas tienen `operation_id`, `response_model` y `tags`?
- [ ] ¿Agregué variables de entorno? ¿Están en `.env.example` con comentario?
- [ ] ¿Agregué dependencias nuevas? ¿Están justificadas?
- [ ] ¿Pasaron todos los comandos de la §9?
