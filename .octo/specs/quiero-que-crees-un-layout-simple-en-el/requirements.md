# Requirements — Layout base con navegación (Órdenes y Estrategias)

## Introduction

El frontend (`frontend/`, Vite + React 19 + React Router 8 en modo data + Ant Design 6) hoy expone una única ruta `/` que renderiza `HealthPage`. Esta feature agrega el **layout base** de la app de trading: un logo, un menú lateral y navegación client-side con `react-router` entre las dos primeras secciones, **Órdenes** y **Estrategias**. Ambas secciones son, por ahora, cáscaras vacías: solo un título que identifica la sección.

Decisiones tomadas en este borrador (confirmar en la revisión):

- **Rutas**: `/ordenes` y `/estrategias` (sin acentos en la URL); etiquetas visibles «Órdenes» y «Estrategias».
- **Ruta raíz**: `/` redirige a `/ordenes`.
- **`HealthPage`**: se conserva, se mueve a `/health` dentro del layout y **no** aparece en el menú. Sus `data-testid` (`health-loading`, `health-status`, `health-database`, `health-error`) se mantienen; el test e2e pasa a abrir `/health`.
- **Logo**: no existe un asset gráfico en el repo; el logo es el texto «Matriz Trader» (un asset de imagen queda fuera de alcance).
- **Rutas desconocidas**: redirigen a `/ordenes`.

## User Stories

- **US-1**: Como usuario de la app de trading, quiero ver un layout consistente con el logo y un menú lateral en todas las pantallas, para orientarme siempre dentro de la app.
- **US-2**: Como usuario, quiero navegar entre Órdenes y Estrategias desde el menú lateral sin recargar la página, para moverme rápido entre secciones.
- **US-3**: Como usuario, quiero que cada sección tenga su propia URL (enlazable, recargable y compatible con atrás/adelante del navegador), para volver directo a una sección.
- **US-4**: Como desarrollador, quiero que las secciones Órdenes y Estrategias existan como páginas vacías con ruta propia, para construir su contenido en features posteriores.
- **US-5**: Como desarrollador/operador, quiero seguir accediendo a la página de estado (`HealthPage`) y que los tests e2e sigan pasando, para no perder el chequeo de salud del stack.

## Acceptance Criteria (EARS)

### Layout

- AC-1: WHEN el usuario abre cualquier ruta de la app (`/ordenes`, `/estrategias`, `/health`) THEN the system SHALL renderizar un layout compuesto por un área de logo, un menú lateral y un área de contenido, implementado con `Layout`/`Layout.Sider`/`Layout.Content` de Ant Design. (US-1)
- AC-2: WHEN se renderiza el layout THEN the system SHALL mostrar el logo como el texto «Matriz Trader» con `data-testid="app-logo"` en la parte superior del menú lateral. (US-1)
- AC-3: WHEN el usuario hace clic en el logo THEN the system SHALL navegar a `/ordenes` sin recargar el documento. (US-1, US-2)
- AC-4: WHEN se renderiza el layout THEN the system SHALL mostrar un menú lateral (`data-testid="app-menu"`, componente `Menu` de antd en modo `inline`) con exactamente dos ítems, en este orden: «Órdenes» y «Estrategias». (US-1, US-2)
- AC-5: WHEN el usuario navega entre secciones THEN the system SHALL mantener montados el logo y el menú lateral (solo cambia el contenido renderizado a través del `<Outlet />` del layout). (US-1, US-2)

### Navegación

- AC-6: WHEN el usuario hace clic en el ítem «Órdenes» del menú THEN the system SHALL cambiar la URL a `/ordenes` y renderizar la página de Órdenes sin recarga completa del documento. (US-2)
- AC-7: WHEN el usuario hace clic en el ítem «Estrategias» del menú THEN the system SHALL cambiar la URL a `/estrategias` y renderizar la página de Estrategias sin recarga completa del documento. (US-2)
- AC-8: WHILE la URL actual es `/ordenes` THE system SHALL marcar como seleccionado únicamente el ítem «Órdenes» del menú. (US-2, US-3)
- AC-9: WHILE la URL actual es `/estrategias` THE system SHALL marcar como seleccionado únicamente el ítem «Estrategias» del menú. (US-2, US-3)
- AC-10: WHILE la URL actual es `/health` THE system SHALL no marcar ningún ítem del menú como seleccionado. (US-5)
- AC-11: WHEN el usuario abre `/` THEN the system SHALL redirigir (reemplazando la entrada del historial) a `/ordenes`. (US-3)
- AC-12: WHEN el usuario abre una ruta que no coincide con ninguna definida THEN the system SHALL redirigir (reemplazando la entrada del historial) a `/ordenes`. (US-3)
- AC-13: WHEN el usuario usa atrás/adelante del navegador después de navegar entre secciones THEN the system SHALL renderizar la sección correspondiente a la URL y actualizar el ítem seleccionado del menú en consecuencia. (US-3)
- AC-14: WHEN el usuario carga directamente (o recarga) `/ordenes` o `/estrategias` en el build de producción servido por nginx (`http://localhost:8080`) THEN the system SHALL responder HTTP 200 y renderizar esa sección dentro del layout. (US-3)

### Secciones vacías

- AC-15: WHEN se renderiza la ruta `/ordenes` THEN the system SHALL mostrar en el área de contenido un título «Órdenes» con `data-testid="page-ordenes"` y ningún otro contenido funcional. (US-4)
- AC-16: WHEN se renderiza la ruta `/estrategias` THEN the system SHALL mostrar en el área de contenido un título «Estrategias» con `data-testid="page-estrategias"` y ningún otro contenido funcional. (US-4)
- AC-17: IF las páginas de Órdenes o Estrategias se renderizan THEN the system SHALL no realizar ninguna request HTTP al backend desde esas páginas. (US-4)

### HealthPage

- AC-18: WHEN el usuario abre `/health` THEN the system SHALL renderizar `HealthPage` dentro del área de contenido del layout, conservando los `data-testid` `health-loading`, `health-status`, `health-database` y `health-error`. (US-5)
- AC-19: WHEN se ejecuta `uv run pytest e2e` con el stack levantado THEN the system SHALL pasar la suite abriendo `/health` en lugar de `/` para el chequeo de salud. (US-5)

### Tests

- AC-20: WHEN se ejecuta `npm test` en `frontend/` THEN the system SHALL incluir tests (Vitest + Testing Library, con un router en memoria) que verifiquen AC-4, AC-6, AC-7, AC-8, AC-9, AC-11, AC-12, AC-15 y AC-16, y todos SHALL pasar. (US-1, US-2, US-3, US-4)
- AC-21: WHEN se ejecuta la suite e2e THEN the system SHALL incluir un test de Playwright que, partiendo de `/`, verifique la redirección a `/ordenes`, el clic en «Estrategias» (URL `/estrategias` y `page-estrategias` visible) y la recarga directa de `/estrategias` (AC-14). (US-2, US-3)

## Out of Scope

- Contenido funcional de Órdenes y Estrategias (listados, formularios, llamadas a la API, market data).
- Cambios en backend, worker, modelo de datos u `openapi.json`.
- Logo como imagen/asset gráfico, favicon, branding o tema visual propio (se usa el tema por defecto de antd).
- Menú colapsable, comportamiento responsive/mobile específico y modo oscuro.
- Header/top bar, breadcrumbs, footer, títulos de pestaña (`document.title`) por sección.
- Autenticación, login, control de acceso por ruta o usuario en la UI.
- Página 404 dedicada (las rutas desconocidas redirigen, AC-12).
- Entrada de menú para `HealthPage`.
- Lazy loading / code splitting de rutas.

## Non-Functional Requirements

- NFR-1: La navegación entre secciones es 100 % client-side vía `react-router` (`createBrowserRouter` con una ruta layout y rutas hijas); el documento no se recarga al cambiar de sección (verificable en Playwright: el `window` conserva una marca seteada antes del clic).
- NFR-2: Los cambios se limitan a `frontend/` y `e2e/` (más la documentación en `frontend/CLAUDE.md` y `e2e/CLAUDE.md` sobre rutas y `data-testid` nuevos).
- NFR-3: No se agregan dependencias npm nuevas; se usan `react-router` y `antd` ya instalados.
- NFR-4: `scripts/check.sh` termina con exit 0 (Biome, ESLint, `tsc -b` strict, Vitest, Ruff y Pyright sobre el e2e modificado).
- NFR-5: Los `data-testid` nuevos (`app-logo`, `app-menu`, `page-ordenes`, `page-estrategias`) y los existentes de `HealthPage` se documentan como contrato de los tests en `frontend/CLAUDE.md`.
- NFR-6: El cambio de sección tras un clic en el menú renderiza el contenido nuevo en menos de 100 ms en el build de producción (medido en Playwright entre el clic y la visibilidad del `data-testid` de la página).

## Open Questions
- [ ] ¿Cómo se verifica NFR-6 (cambio de sección en menos de 100 ms) en Playwright?
  - Se omite como assert y se cubre con NFR-1 (sin recarga del documento) — evita un test inestable en CI o en máquinas lentas
  - Assert con un umbral holgado (p. ej. 500 ms) — conserva una guarda de rendimiento con menos falsos negativos
  - Assert estricto de 100 ms, como dice el requisito — cumple el texto, pero puede fallar sin que haya un problema real
- [x] ¿Qué idioma usan los paths de las rutas? — **Resolved:** Inglés (`/orders`, `/strategies`) — sigue la convención habitual en código y API, pero no coincide con lo que ve el usuario
  - Español sin acentos (`/ordenes`, `/estrategias`) — coincide con las etiquetas y con el borrador actual
  - Inglés (`/orders`, `/strategies`) — sigue la convención habitual en código y API, pero no coincide con lo que ve el usuario
- [x] ¿Dónde vive `HealthPage`? — **Resolved:** En `/health`, como tercer ítem de menú — más fácil de descubrir, pero contradice AC-4 («exactamente dos ítems»)
  - En `/health`, dentro del layout y sin ítem de menú — es lo que propone el borrador y queda consistente visualmente
  - En `/health`, fuera del layout (página suelta) — queda aislada de cambios futuros del layout, pero no cumple AC-1 para `/health`
  - En `/health`, como tercer ítem de menú — más fácil de descubrir, pero contradice AC-4 («exactamente dos ítems»)
- [x] ¿Cómo se implementa la navegación desde los ítems del `Menu` de antd? — **Resolved:** La etiqueta de cada ítem es un `<Link>` de react-router — son anchors reales, así que funcionan el clic medio, «abrir en pestaña nueva» y la accesibilidad
  - La etiqueta de cada ítem es un `<Link>` de react-router — son anchors reales, así que funcionan el clic medio, «abrir en pestaña nueva» y la accesibilidad
  - `onClick` del `Menu` que llama a `navigate(key)` — es más simple, pero los ítems no son links reales

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Qué idioma usan los paths de las rutas?** — Inglés (`/orders`, `/strategies`) — sigue la convención habitual en código y API, pero no coincide con lo que ve el usuario
- **¿Dónde vive `HealthPage`?** — En `/health`, como tercer ítem de menú — más fácil de descubrir, pero contradice AC-4 («exactamente dos ítems»)
- **¿Cómo se implementa la navegación desde los ítems del `Menu` de antd?** — La etiqueta de cada ítem es un `<Link>` de react-router — son anchors reales, así que funcionan el clic medio, «abrir en pestaña nueva» y la accesibilidad
