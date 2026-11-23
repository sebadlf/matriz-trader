# Requirements: Bases del proyecto matriz-trader (setup inicial)

## Introduction

`matriz-trader` será un cliente de trading que consume las librerías internas `market-data-client` (v0.7.1) y `matriz-client` (v0.4.0) del repositorio `gravity-quant/market-libs`. Esta primera etapa **solo** establece el esqueleto del monorepo — un módulo `backend/` (Python 3.13 + FastAPI) y un módulo `frontend/` (React + TypeScript + Vite+) — junto con PostgreSQL, Docker Compose para dev y producción, un único `.env` en la raíz, y la documentación `CLAUDE.md` y `README.md`. No se implementa ninguna funcionalidad de negocio.

El criterio de éxito es que un desarrollador pueda clonar el repo, configurar el `.env`, levantar cada parte por separado (local o con Docker Compose) y que todas las herramientas de calidad (lint, formato, tipado, tests) corran en verde sobre el esqueleto vacío.

Notas de formato: las palabras clave de las historias (`As a`, `I want`, `so that`) y de EARS (`WHEN`, `WHILE`, `IF`, `THEN`, `the system SHALL`) se mantienen en inglés porque Octo las parsea literalmente. "El sistema" se refiere al repositorio y sus herramientas.

## User Stories

- US-1: As a desarrollador, I want un monorepo con los módulos `backend/` y `frontend/` y un único `.env` en la raíz ignorado por git, so that la configuración esté centralizada y ningún secreto se versione.
- US-2: As a desarrollador backend, I want un proyecto Python 3.13 con FastAPI, SQLAlchemy 2.0, Pydantic y uv, con `market-data-client` y `matriz-client` instaladas, so that pueda empezar a implementar funcionalidades sin tener que configurar nada.
- US-3: As a desarrollador backend, I want Ruff (lint, formato y reglas ANN) y mypy en modo strict con el plugin `pydantic.mypy` configurados, so that todo el código Python esté tipado y con estilo uniforme desde el primer commit.
- US-4: As a desarrollador frontend, I want un proyecto React + TypeScript sobre Vite+ (`vp`) con Ant Design, React Router y Zustand, organizado en carpetas modulares (screens, components, hooks, utils, api, stores, etc.), so that cada pieza nueva tenga un lugar definido.
- US-5: As a desarrollador frontend, I want que el acceso al backend se haga exclusivamente con un cliente generado por Orval (variante react-query) a partir del OpenAPI del backend, so that los cambios de contrato aparezcan como errores de tipo y no como bugs en runtime.
- US-6: As a desarrollador frontend, I want `vp lint`, `vp fmt`, `vp test` (Vitest + React Testing Library) y Playwright configurados, so that pueda escribir tests unitarios, de integración y e2e sin setup adicional.
- US-7: As a desarrollador, I want levantar PostgreSQL, el backend y el frontend con Docker Compose en modo dev o producción, por separado o juntos, so that el entorno sea reproducible en cualquier máquina.
- US-8: As a desarrollador o agente de IA que se suma al proyecto, I want un `CLAUDE.md` con las convenciones y comandos del proyecto y un `README.md` con la información de instalación y uso, so that pueda trabajar en el repo sin preguntar cómo está armado.

## Acceptance Criteria (EARS notation)

- AC-1: WHEN se inspecciona la raíz del repositorio THEN the system SHALL contener los directorios `backend/` y `frontend/`, un `docker-compose.yml` (o archivos compose equivalentes), `CLAUDE.md`, `README.md`, `.gitignore` y `.env.example`. (US-1)
- AC-2: WHEN se ejecuta `git check-ignore .env` en la raíz THEN the system SHALL reportar el archivo como ignorado. (US-1)
- AC-3: WHEN se busca en el repositorio cualquier archivo `.env` distinto del de la raíz (por ejemplo `backend/.env` o `frontend/.env`) THEN the system SHALL no encontrar ninguno; backend, frontend y Docker Compose SHALL leer su configuración del `.env` de la raíz. (US-1)
- AC-4: WHEN se compara `.env.example` con las variables que leen backend, frontend y Docker Compose THEN the system SHALL listar en `.env.example` cada variable usada, con un valor de ejemplo no secreto y un comentario que explique su propósito. (US-1)
- AC-5: WHEN se ejecuta `uv sync` dentro de `backend/` con acceso SSH a `github.com/gravity-quant/market-libs` THEN the system SHALL crear el virtualenv con Python 3.13 e instalar `fastapi`, `sqlalchemy`, `pydantic`, `market-data-client` en el tag `market-data-client-v0.7.1` y `matriz-client` en el tag `matriz-client-v0.4.0`. (US-2)
- AC-6: WHEN se ejecuta `uv run python -c "import market_data_client, matriz_client"` (o los nombres de módulo reales de esas librerías) dentro de `backend/` THEN the system SHALL terminar con código de salida 0. (US-2)
- AC-7: IF el desarrollador no tiene acceso SSH al repositorio `gravity-quant/market-libs` THEN the system SHALL fallar `uv sync` con código de salida distinto de 0, y `README.md` SHALL documentar ese requisito de acceso en la sección de instalación. (US-2)
- AC-8: WHEN se inicia el backend THEN the system SHALL cargar su configuración desde el `.env` de la raíz mediante un modelo de settings de Pydantic tipado. (US-2)
- AC-9: IF falta una variable de entorno obligatoria o tiene un formato inválido al iniciar el backend THEN the system SHALL abortar el arranque con código de salida distinto de 0 y un mensaje que nombre la variable afectada. (US-2)
- AC-10: WHEN el backend está en ejecución THEN the system SHALL servir el esquema OpenAPI de FastAPI en una URL documentada en `README.md`. (US-2, US-5)
- AC-11: WHEN se inspecciona la capa de base de datos del backend THEN the system SHALL contener una base declarativa de SQLAlchemy 2.0 y una fábrica de sesiones configuradas contra PostgreSQL a partir de la URL definida en el `.env`, sin ningún modelo de negocio. (US-2)
- AC-12: WHEN se ejecutan `uv run ruff check .` y `uv run ruff format --check .` dentro de `backend/` THEN the system SHALL terminar ambos con código de salida 0. (US-3)
- AC-13: WHEN se inspecciona la configuración de Ruff THEN the system SHALL tener habilitadas las reglas `ANN` sin excepciones a nivel de proyecto. (US-3)
- AC-14: IF se agrega una función sin anotaciones de tipo en parámetros o retorno THEN the system SHALL hacer fallar `uv run ruff check .` con una violación `ANN`. (US-3)
- AC-15: WHEN se ejecuta `uv run mypy .` dentro de `backend/` THEN the system SHALL terminar con código de salida 0 usando `strict = true` y el plugin `pydantic.mypy`, y sin el plugin de mypy de SQLAlchemy. (US-3)
- AC-16: WHEN se inspeccionan los modelos de SQLAlchemy del esqueleto THEN the system SHALL declarar las columnas con `Mapped[...]` y `mapped_column()`. (US-3)
- AC-17: WHEN se ejecuta `vp install` (o el comando de instalación documentado) y luego `vp build` dentro de `frontend/` THEN the system SHALL instalar las dependencias y generar el build de producción con código de salida 0. (US-4)
- AC-18: WHEN se inspecciona `frontend/package.json` THEN the system SHALL declarar como dependencias `react`, `react-dom`, `typescript`, `antd`, `react-router` (o `react-router-dom`), `zustand`, `@tanstack/react-query` y `orval`, y SHALL no declarar ESLint, Prettier, Jest ni otro cliente HTTP, gestor de estado o librería de componentes. (US-4)
- AC-19: WHEN se inspecciona `frontend/src/` THEN the system SHALL contener los directorios `app/`, `api/`, `screens/`, `components/`, `layouts/`, `hooks/`, `stores/`, `utils/`, `constants/`, `types/` y `test/`. (US-4)
- AC-20: WHEN se abre el frontend en el navegador THEN the system SHALL renderizar la aplicación dentro de `ConfigProvider` y `App` de Ant Design, un `QueryClientProvider` y el router de React Router. (US-4)
- AC-21: WHEN se navega a una ruta no definida del frontend THEN the system SHALL mostrar una pantalla 404. (US-4)
- AC-22: WHEN se inspecciona `frontend/tsconfig*.json` THEN the system SHALL tener `strict: true` y el alias `@/` apuntando a `src/`. (US-4)
- AC-23: WHEN se ejecuta `vp run generate:api` dentro de `frontend/` THEN the system SHALL generar con Orval, usando `client: 'react-query'`, el cliente tipado en `frontend/src/api/generated/` a partir del OpenAPI del backend, con todas las llamadas HTTP pasando por un único mutator en `frontend/src/api/`. (US-5)
- AC-24: IF el esquema OpenAPI del backend no está disponible cuando se ejecuta `vp run generate:api` THEN the system SHALL terminar con código de salida distinto de 0 y un mensaje que indique la fuente que no se pudo leer. (US-5)
- AC-25: WHEN se busca en `frontend/src/` fuera de `src/api/` cualquier uso de `fetch(` o de `axios` THEN the system SHALL no encontrar ninguno. (US-5)
- AC-26: WHEN se ejecutan `vp lint` y `vp fmt --check` dentro de `frontend/` THEN the system SHALL terminar ambos con código de salida 0. (US-6)
- AC-27: WHEN se ejecuta `vp test run` dentro de `frontend/` THEN the system SHALL ejecutar con Vitest y React Testing Library al menos un test de ejemplo usando un helper de render común en `src/test/`, y terminar con código de salida 0. (US-6)
- AC-28: WHEN se ejecuta `vp run e2e` dentro de `frontend/` THEN the system SHALL ejecutar con Playwright al menos un test de ejemplo ubicado en `frontend/e2e/` que abra la aplicación, y terminar con código de salida 0. (US-6)
- AC-29: WHEN se ejecuta Docker Compose en modo dev THEN the system SHALL levantar PostgreSQL, el backend con recarga automática ante cambios en `backend/` y el frontend con el servidor de desarrollo de `vp` y recarga ante cambios en `frontend/`. (US-7)
- AC-30: WHEN se ejecuta Docker Compose en modo producción THEN the system SHALL construir imágenes del backend y del frontend sin dependencias ni servidores de desarrollo, y levantarlas junto con PostgreSQL. (US-7)
- AC-31: WHEN se levanta con Docker Compose solo el servicio de backend o solo el de frontend, en cualquiera de los dos modos THEN the system SHALL iniciar ese servicio (y PostgreSQL, si el servicio lo requiere) sin iniciar el otro. (US-7)
- AC-32: WHEN se levantan los servicios con Docker Compose THEN the system SHALL tomar las variables de entorno del `.env` de la raíz y persistir los datos de PostgreSQL en un volumen con nombre. (US-1, US-7)
- AC-33: IF el `.env` de la raíz no existe al ejecutar Docker Compose THEN the system SHALL fallar con un mensaje que indique copiar `.env.example` a `.env`. (US-7)
- AC-34: IF la clave SSH para `gravity-quant/market-libs` no está disponible al construir la imagen del backend THEN the system SHALL fallar el build con código de salida distinto de 0, y `README.md` SHALL documentar cómo proveer la clave al build (por ejemplo con `--ssh default`) sin copiarla dentro de la imagen. (US-7)
- AC-35: WHEN se inspecciona `CLAUDE.md` THEN the system SHALL documentar el stack de cada módulo, la estructura de carpetas y sus reglas de dependencia, los comandos de desarrollo, calidad y tests de cada módulo, el flujo de regeneración del cliente Orval y la regla de que el frontend accede al backend únicamente mediante Orval. (US-8)
- AC-36: WHEN se inspecciona `README.md` THEN the system SHALL documentar la descripción del proyecto, los prerrequisitos (Python 3.13, uv, Node/Vite+, Docker, acceso SSH a `market-libs`), la configuración del `.env`, cómo iniciar cada parte localmente y con Docker Compose en modo dev y producción, y cómo ejecutar lint, formato, tipado y tests. (US-8)
- AC-37: WHEN un desarrollador ejecuta, en orden, cada comando documentado en `README.md` sobre un clon limpio con un `.env` copiado de `.env.example` THEN the system SHALL completar cada comando con código de salida 0. (US-8)

## Out of Scope

- Cualquier funcionalidad de negocio o de trading: pantallas, endpoints, modelos de dominio o uso real de `market-data-client` / `matriz-client` más allá de instalarlas e importarlas.
- Autenticación, autorización y manejo de usuarios.
- Pipelines de CI/CD y despliegue a un entorno remoto.
- Internacionalización, theming propio más allá del `ConfigProvider` base, y diseño visual.
- Migraciones con datos o tablas de dominio (ver Open Questions sobre Alembic).
- Observabilidad (métricas, tracing, logging centralizado).

## Non-Functional Requirements

- NFR-1: Las versiones de `market-data-client` (`market-data-client-v0.7.1`) y `matriz-client` (`matriz-client-v0.4.0`) quedan fijadas por tag en `backend/pyproject.toml` y en `uv.lock`, ambos versionados.
- NFR-2: Los lockfiles (`backend/uv.lock` y el lockfile del frontend) se versionan para que las instalaciones sean reproducibles.
- NFR-3: Ningún secreto (contraseñas, claves SSH, tokens) se incluye en archivos versionados ni en capas de las imágenes Docker.
- NFR-4: La configuración de lint, formato y tests del frontend vive en `frontend/vite.config.ts`, sin archivos de configuración paralelos de Oxlint, Oxfmt o Vitest.
- NFR-5: La configuración de Ruff y mypy vive en `backend/pyproject.toml`.
- NFR-6: `frontend/src/api/generated/` se marca como código generado: excluido de lint y formato, y documentado en `CLAUDE.md` como no editable a mano.
- NFR-7: Los comandos de calidad de ambos módulos (AC-12, AC-15, AC-26, AC-27) terminan en menos de 60 s cada uno sobre el esqueleto vacío en una máquina de desarrollo típica.

## Open Questions
- [x] ¿Qué endpoint mínimo usamos para validar de punta a punta el pipeline Orval → frontend → Playwright? — **Resolved:** Elijo `GET /api/health` solo con el estado del servicio, sin chequear la DB. Alcanza para validar el pipeline Orval → frontend → Playwright, y el test e2e no depende de PostgreSQL.
  - `GET /api/health` solo con el estado del servicio, sin chequear la DB — más simple y estable, pero no valida la conexión a PostgreSQL.
- [x] ¿De dónde lee Orval el esquema OpenAPI cuando se ejecuta `generate:api`? — **Resolved:** Orval lee un archivo `openapi.json` versionado en `backend/openapi.json`. Ese archivo se genera con un script del backend, `uv run python -m app.scripts.export_openapi`, que vuelca `app.openapi()` sin levantar el servidor ni conectarse a PostgreSQL. `frontend/orval.config.ts` toma esa ruta (`../backend/openapi.json`) como `input`, así que `vp run generate:api` funciona sin backend en ejecución, es reproducible y no depende de la red ni de la DB. Si el archivo falta o está mal formado, Orval termina con código distinto de 0 y muestra la ruta que no pudo leer, lo que cumple AC-24. `CLAUDE.md` debe documentar el flujo en este orden: cambiar endpoints, exportar el esquema, ejecutar `generate:api` y commitear los dos resultados.
- [x] ¿Incluimos Alembic en esta etapa? — **Resolved:** **Recomendación:** dejar Alembic para cuando exista el primer modelo de dominio. Así el esqueleto queda más chico, pero después habrá que configurarlo en medio de una feature.

**Por qué:** el esqueleto no tiene ningún modelo de negocio (AC-11) y las migraciones ya figuran en Out of Scope. Configurar Alembic ahora sumaría herramientas que nadie usaría todavía y que habría que mantener en verde.
  - Postergarlo hasta el primer modelo de dominio — el esqueleto queda más chico, pero después hay que hacer el setup a mitad de una feature.
- [x] ¿Cómo se sirve el frontend en modo producción? — **Resolved:** Ninguna de las dos opciones sirve. FastAPI sirviendo los estáticos contradice AC-31, y `vp preview` contradice AC-30, que exige imágenes sin servidores de desarrollo. Conviene un contenedor nginx que sirva el build estático y haga proxy de `/api` al backend.
  - FastAPI sirve los estáticos del build — un servicio menos, pero acopla las imágenes y contradice que cada parte se pueda levantar por separado (AC-31).
  - Contenedor Node/`vp preview` — reutiliza el tooling, pero lo hace con un servidor que no está pensado para producción.
- [x] ¿Cómo se estructuran los modos dev y producción de Docker Compose? — **Resolved:** **Dos archivos independientes y completos.** Cada modo queda fácil de leer por separado, cumple AC-29 a AC-32 sin depender de cómo se combinan varios archivos, y repetir la configuración de PostgreSQL y de los volúmenes es un costo menor en un esqueleto de solo tres servicios.
  - Dos archivos independientes y completos — cada uno es fácil de leer, pero duplica la configuración de PostgreSQL y los volúmenes.
- [x] ¿Qué framework de tests usamos para el backend? — **Resolved:** **Opción elegida:** `pytest` + `pytest-asyncio` con `httpx.AsyncClient`. Está listo para endpoints y sesiones async, aunque suma configuración que el esqueleto todavía no necesita.

**Por qué:** deja al backend con el mismo nivel de calidad que el frontend (AC-27) y permite agregar un test de ejemplo para `GET /api/health`.
  - `pytest` + `pytest-asyncio` con `httpx.AsyncClient` — está listo para endpoints y sesiones async, pero suma configuración que el esqueleto todavía no necesita.
  - Sin tests de backend en esta etapa — menos alcance, pero queda un hueco frente a los criterios de calidad del frontend.

1. **Endpoint mínimo para validar el pipeline.** Orval necesita al menos un endpoint en el OpenAPI para generar algo, y Docker Compose/Playwright necesitan algo que comprobar. ¿Aceptás un único `GET /api/health` (que devuelva el estado del servicio y de la conexión a PostgreSQL) y una pantalla de inicio que lo consuma vía Orval, como única "funcionalidad" de infraestructura? *Default propuesto: sí.*
2. **Migraciones.** ¿Incluimos Alembic configurado (sin migraciones de dominio) en esta etapa, o lo dejamos para cuando exista el primer modelo? *Default propuesto: incluir Alembic configurado y vacío.*
3. **Frontend en producción.** ¿Cómo se sirve el build estático del frontend en modo producción: un contenedor nginx que además hace proxy de `/api` al backend, o el backend sirviendo los estáticos? *Default propuesto: nginx con proxy de `/api`.*
4. **Tests del backend.** No se especificó framework de tests para Python. ¿Usamos `pytest` (con `httpx` para el `TestClient` de FastAPI)? *Default propuesto: sí, con un test de ejemplo y su criterio correspondiente.*

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Qué endpoint mínimo usamos para validar de punta a punta el pipeline Orval → frontend → Playwright?** — Elijo `GET /api/health` solo con el estado del servicio, sin chequear la DB. Alcanza para validar el pipeline Orval → frontend → Playwright, y el test e2e no depende de PostgreSQL.
- **¿De dónde lee Orval el esquema OpenAPI cuando se ejecuta `generate:api`?** — Orval lee un archivo `openapi.json` versionado en `backend/openapi.json`. Ese archivo se genera con un script del backend, `uv run python -m app.scripts.export_openapi`, que vuelca `app.openapi()` sin levantar el servidor ni conectarse a PostgreSQL. `frontend/orval.config.ts` toma esa ruta (`../backend/openapi.json`) como `input`, así que `vp run generate:api` funciona sin backend en ejecución, es reproducible y no depende de la red ni de la DB. Si el archivo falta o está mal formado, Orval termina con código distinto de 0 y muestra la ruta que no pudo leer, lo que cumple AC-24. `CLAUDE.md` debe documentar el flujo en este orden: cambiar endpoints, exportar el esquema, ejecutar `generate:api` y commitear los dos resultados.
- **¿Incluimos Alembic en esta etapa?** — **Recomendación:** dejar Alembic para cuando exista el primer modelo de dominio. Así el esqueleto queda más chico, pero después habrá que configurarlo en medio de una feature.
- **¿Cómo se sirve el frontend en modo producción?** — Ninguna de las dos opciones sirve. FastAPI sirviendo los estáticos contradice AC-31, y `vp preview` contradice AC-30, que exige imágenes sin servidores de desarrollo. Conviene un contenedor nginx que sirva el build estático y haga proxy de `/api` al backend.
- **¿Cómo se estructuran los modos dev y producción de Docker Compose?** — **Dos archivos independientes y completos.** Cada modo queda fácil de leer por separado, cumple AC-29 a AC-32 sin depender de cómo se combinan varios archivos, y repetir la configuración de PostgreSQL y de los volúmenes es un costo menor en un esqueleto de solo tres servicios.
- **¿Qué framework de tests usamos para el backend?** — **Opción elegida:** `pytest` + `pytest-asyncio` con `httpx.AsyncClient`. Está listo para endpoints y sesiones async, aunque suma configuración que el esqueleto todavía no necesita.
