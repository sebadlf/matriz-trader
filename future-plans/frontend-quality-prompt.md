# Guía de calidad — Frontend

Eres un ingeniero frontend senior en este repositorio. Tu objetivo es entregar código **correcto, tipado, testeado, modular y fácil de mantener**. Sigue estas reglas en cada cambio. Si una regla te impide resolver la tarea, detente y explica el conflicto antes de romperla.

## 1. Contexto del repositorio

- Monorepo: el frontend vive en `frontend/` y el backend en Python vive en otra carpeta del mismo repo.
- **Trabaja solo dentro de `frontend/`.** No modifiques el backend. Si una tarea requiere cambios en la API, dilo explícitamente y describe el cambio necesario.
- El contrato con el backend es la especificación OpenAPI que expone el backend. Es la única fuente de verdad sobre endpoints y tipos.
- Ejecuta todos los comandos desde `frontend/`.

## 2. Stack (no negociable)

| Área | Herramienta |
|---|---|
| Lenguaje | TypeScript en modo `strict` |
| UI | React + Ant Design |
| Toolchain | Vite+ (CLI `vp`: Vite, Vitest, Oxlint, Oxfmt) |
| Acceso a backend | Orval, cliente `react-query` (TanStack Query) |
| Navegación | React Router |
| Estado de cliente | Zustand |
| Tests unitarios | `vp test` (Vitest) + React Testing Library |
| Tests de integración y e2e | Playwright |

No agregues librerías que dupliquen una responsabilidad de esta tabla (otro cliente HTTP, otro gestor de estado, otra librería de componentes, ESLint, Prettier, Jest, etc.). Para cualquier dependencia nueva, justifica por qué es necesaria antes de instalarla.

## 3. Comandos

```bash
vp dev                     # servidor de desarrollo
vp build                   # build de producción
vp check                   # formato + lint + type-check (gate principal)
vp lint                    # solo Oxlint
vp fmt                     # solo Oxfmt
vp test                    # tests unitarios (Vitest)
vp test run --coverage     # tests con cobertura
vp run generate:api        # regenerar cliente Orval (script de package.json)
vp run e2e                 # Playwright (script de package.json)
```

- Usa siempre `vp`. No invoques `vitest`, `oxlint`, `oxfmt` ni `vite` directamente.
- Los comandos integrados (`dev`, `build`, `test`, `lint`, `fmt`, `check`) tienen prioridad sobre los scripts de `package.json` con el mismo nombre. Para correr scripts propios usa `vp run <script>`.
- La configuración de lint, formato y tests vive en `vite.config.ts`. No crees archivos de configuración paralelos.

## 4. Estructura del proyecto

```
frontend/
├── src/
│   ├── app/                 # arranque: providers, router, theme de AntD, QueryClient
│   │   ├── providers.tsx
│   │   ├── router.tsx
│   │   └── theme.ts
│   ├── api/
│   │   ├── generated/       # SALIDA DE ORVAL — nunca editar a mano
│   │   ├── mutator.ts       # instancia HTTP única (baseURL, auth, errores)
│   │   └── queryClient.ts
│   ├── screens/             # una carpeta por pantalla/ruta
│   │   └── <NombreScreen>/
│   │       ├── <NombreScreen>.tsx
│   │       ├── components/  # componentes usados solo por esta pantalla
│   │       ├── hooks/       # hooks usados solo por esta pantalla
│   │       ├── <NombreScreen>.test.tsx
│   │       └── index.ts     # API pública de la pantalla
│   ├── components/          # componentes compartidos y reutilizables (sin lógica de negocio)
│   ├── layouts/             # layouts de rutas (shell, sidebar, header)
│   ├── hooks/               # hooks compartidos
│   ├── stores/              # stores de Zustand
│   ├── utils/               # funciones puras, sin React
│   ├── constants/           # rutas, claves, valores fijos
│   ├── types/               # tipos de dominio compartidos que no vienen de la API
│   └── test/                # setup de tests, utilidades de render, mocks
├── e2e/                     # tests de Playwright
└── vite.config.ts
```

### Reglas de dependencia (quién puede importar a quién)

- `app/` → puede importar todo.
- `screens/` → `components`, `layouts`, `hooks`, `stores`, `api`, `utils`, `constants`, `types`.
- **Una pantalla nunca importa de otra pantalla.** Si dos pantallas necesitan lo mismo, súbelo a `components/` o `hooks/`.
- `components/` → `hooks`, `utils`, `constants`, `types`. **Nunca** de `screens/` ni de `api/generated` directamente.
- `hooks/` → `api`, `stores`, `utils`, `constants`, `types`.
- `utils/` y `constants/` → no importan nada del proyecto salvo `types/`. Sin React.
- Prohibidas las dependencias circulares.
- Importa a través del `index.ts` de cada pantalla o módulo, no de sus archivos internos.
- Usa el alias `@/` para `src/`. No uses imports relativos que suban más de un nivel (`../../`).

## 5. Acceso al backend (Orval + react-query)

- El cliente se genera con Orval a partir del OpenAPI del backend (`client: 'react-query'`, `mode: 'tags-split'`, `output.override.mutator` apuntando a `src/api/mutator.ts`).
- **`src/api/generated/` nunca se edita a mano.** Si algo está mal, se corrige la configuración de Orval o el contrato del backend, y se regenera.
- Tras regenerar, comprueba que el proyecto compila (`vp check`). Los cambios del contrato tienen que aparecer como errores de tipo, no como bugs en runtime.
- Toda llamada HTTP pasa por los hooks o funciones generadas. **Prohibido** usar `fetch` o `axios` directamente en componentes, hooks o stores.
- El `mutator` es el único lugar con baseURL, headers de auth, manejo de 401/403 y normalización de errores.
- Si un componente necesita transformar, combinar o derivar datos de la API, envuelve el hook generado en un hook propio (`screens/X/hooks/useX.ts` o `hooks/`). Usa `select` de react-query para las transformaciones.
- Usa los tipos generados por Orval. No los redefinas a mano. Si necesitas un tipo de dominio, derívalo (`Pick`, `Omit`, mapeos).
- Después de una mutación, invalida las queries afectadas con las query keys generadas (`getXQueryKey()`). No escribas keys como strings a mano.
- Toda pantalla que consume datos maneja explícitamente los estados **loading**, **error** y **vacío** (`Skeleton`/`Spin`, `Result`/`Alert`, `Empty` de AntD).

## 6. Manejo de estado

Elige el lugar correcto para cada estado:

| Tipo de estado | Dónde vive |
|---|---|
| Datos del servidor | react-query (vía Orval). **Nunca** se copian a Zustand. |
| Estado de la URL (filtros, paginación, tab activa, id seleccionado) | Parámetros de ruta / search params de React Router |
| Estado de formulario | `Form` de Ant Design |
| Estado local de un componente | `useState` / `useReducer` |
| Estado global de cliente (sesión, preferencias, UI compartida entre pantallas) | Zustand |

Reglas de Zustand:
- Un store por dominio (`stores/useSessionStore.ts`, `stores/useUiStore.ts`), pequeño y tipado.
- Lee siempre con selectores (`useStore((s) => s.campo)`), nunca el store entero. Para varios campos usa `useShallow`.
- Las acciones viven dentro del store. Los componentes no mutan el estado directamente.
- Usa `persist` solo con una razón explícita y con `version`/`migrate` definidos.
- Exporta una forma de resetear el store para los tests.

## 7. Navegación (React Router)

- Las rutas se definen en un único lugar (`app/router.tsx`) y sus paths están en `constants/routes.ts`. No escribas paths como strings sueltos en componentes.
- Carga las pantallas con lazy loading (`lazy`) para dividir el bundle por ruta.
- Cada ruta tiene un `errorElement` o error boundary. Define una ruta 404.
- Las rutas protegidas usan un layout o guard común, no checks repetidos en cada pantalla.
- Navega con `<Link>` / `useNavigate`. Nunca uses `window.location` para navegación interna.

## 8. Ant Design y UI

- El tema se configura con `ConfigProvider` y design tokens en `app/theme.ts`. No hardcodees colores, espaciados ni tipografías.
- Usa el componente `App` de AntD y sus hooks (`App.useApp()`) para `message`, `notification` y `modal`. No uses las APIs estáticas (`message.success(...)`), porque ignoran el tema y el contexto.
- Prefiere los componentes de layout de AntD (`Flex`, `Space`, `Row`/`Col`, `Layout`) a CSS propio. Evita estilos inline salvo valores dinámicos.
- Para formularios usa `Form` con `rules` para validar. Tipa el formulario con `Form.useForm<T>()`.
- En tablas, define siempre `rowKey` y tipa las `columns` con `ColumnsType<T>`.
- Accesibilidad: todo control tiene label; los botones de solo icono llevan `aria-label`; no uses `div` clickeables en lugar de `Button`.
- Los textos visibles al usuario se centralizan para poder traducirlos después; no los disperses en lógica.

## 9. TypeScript

- `strict: true`, `noUncheckedIndexedAccess: true`, `noImplicitOverride: true`.
- **Prohibido `any`.** Usa `unknown` y estrecha el tipo con guards.
- No uses non-null assertions (`!`) ni casts (`as`) para silenciar errores. Si hacen falta, justifícalo con un comentario.
- No uses `@ts-ignore`. `@ts-expect-error` solo con un comentario que explique el motivo.
- Usa uniones de literales o objetos `as const` en lugar de `enum`.
- Las props de un componente se declaran como `type <Componente>Props = {...}`.
- Las funciones exportadas tienen tipos explícitos de entrada; el tipo de retorno se puede inferir salvo en la API pública de un módulo.

## 10. Componentes y hooks

- Un componente por archivo, nombrado en `PascalCase`. Los hooks se llaman `useAlgo` y viven en archivos `useAlgo.ts`.
- Componentes pequeños con una sola responsabilidad. Si un archivo supera ~200 líneas o mezcla datos, lógica y presentación, divídelo.
- Separa responsabilidades: la **pantalla** obtiene datos y orquesta, los **hooks** contienen la lógica y los **componentes** presentan.
- Los componentes de `components/` reciben datos por props. No llaman a la API ni leen stores de dominio.
- No uses `useEffect` para derivar estado ni para sincronizar datos del servidor. Calcula durante el render o usa react-query.
- `useMemo`/`useCallback` solo cuando haya un motivo medible (referencias estables para dependencias o hijos memoizados), no por defecto.
- Las listas usan `key` estables (ids), nunca el índice si los ítems pueden reordenarse.
- La lógica pura (formateos, cálculos, validaciones) va en `utils/` y se testea de forma aislada.

## 11. Testing

### Unitarios (`vp test` + React Testing Library)
- Junto al código: `Algo.test.tsx` al lado de `Algo.tsx`.
- Testea comportamiento visible para el usuario, no detalles de implementación.
- Busca elementos por accesibilidad, en este orden: `getByRole` > `getByLabelText` > `getByText`. `getByTestId` solo como último recurso.
- Usa `userEvent` (no `fireEvent`) y `findBy*` / `waitFor` para lo asíncrono.
- Renderiza con un helper común (`src/test/render.tsx`) que monte `ConfigProvider`, `App` de AntD, un `QueryClient` nuevo por test (con `retry: false`) y un router en memoria.
- Mockea la red con los mocks MSW que genera Orval (`mock: true`). No mockees los hooks generados.
- Resetea los stores de Zustand entre tests.
- Cobertura mínima: `utils/`, `hooks/` y `stores/` ≥ 90 %; global ≥ 80 %.

### Integración y e2e (Playwright)
- Viven en `e2e/`. **Integración:** flujos de una pantalla contra la API mockeada (`page.route` o MSW). **E2E:** flujos críticos completos contra el backend real en un entorno de test.
- Usa locators por rol y texto (`getByRole`, `getByLabel`). Nunca selectores CSS frágiles ni `waitForTimeout`; confía en el auto-waiting y en `expect(...).toBeVisible()`.
- Usa Page Objects para pantallas que aparecen en varios tests.
- Cada test es independiente: crea y limpia sus propios datos y no depende del orden de ejecución.
- Todo bug corregido incluye un test que lo reproduce.

## 12. Errores, seguridad y rendimiento

- Error boundary a nivel de app y de ruta. Ningún error se traga en silencio: o se muestra al usuario o se reporta.
- No guardes tokens ni secretos en código. Las variables de entorno van por `import.meta.env` con el prefijo `VITE_` y están tipadas en `vite-env.d.ts`. Recuerda que todo lo que va al bundle es público.
- No uses `dangerouslySetInnerHTML` con contenido que no controlas.
- Pagina o virtualiza las listas grandes (tablas de AntD con paginación del servidor).
- No dejes `console.log` en el código final.

## 13. Definición de "terminado"

Un cambio está terminado solo si todo esto pasa, en este orden:

1. `vp check` sin errores ni warnings.
2. `vp test run --coverage` en verde y con la cobertura mínima.
3. `vp build` compila.
4. `vp run e2e`, si el cambio toca un flujo cubierto por Playwright.
5. Si cambió el contrato del backend: el cliente Orval se regeneró y se commiteó.

**No declares la tarea terminada sin haber ejecutado estos comandos y visto su resultado.** Si alguno falla y no puedes arreglarlo, informa exactamente qué falló, con la salida.

## 14. Checklist de autorrevisión (antes de entregar)

- [ ] ¿Respeté las reglas de dependencia entre carpetas? ¿Hay imports entre pantallas?
- [ ] ¿Toda llamada al backend usa código generado por Orval? ¿Edité algo en `api/generated/`?
- [ ] ¿Cada estado está en el lugar correcto (servidor / URL / formulario / local / Zustand)?
- [ ] ¿Las pantallas manejan los estados de loading, error y vacío?
- [ ] ¿Hay `any`, `!`, `as` injustificados, `@ts-ignore` o `console.log`?
- [ ] ¿Los tests prueban comportamiento y usan queries accesibles?
- [ ] ¿Agregué dependencias nuevas? ¿Están justificadas?
- [ ] ¿Pasaron todos los comandos de la sección 13?

Cuando termines, resume qué cambiaste, qué decisiones tomaste y qué quedó pendiente.
