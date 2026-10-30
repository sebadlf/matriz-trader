# Requirements — Initial setup (Matriz Trader)

## Introduction

Este ticket inicializa el proyecto **Matriz Trader** como un monorepo con cuatro partes: `frontend`, `backend`, `worker` y `model`, más la infraestructura compartida (PostgreSQL, configuración de entorno centralizada, Docker Compose, unit tests y tests de integración).

El alcance es **solo la inicialización**: cada pieza debe existir, compilar/arrancar, pasar lint, formateo, type-check y tests, y comunicarse con las demás de punta a punta mediante un flujo mínimo de verificación ("health"). No se implementa funcionalidad de negocio.

Decisiones tecnológicas fijadas por el usuario (no negociables en este ticket):

| Área | Decisión |
|------|----------|
| Estructura | Monorepo reconocido como tal por VS Code y Claude Code |
| Frontend | Vite, React, React Router, TypeScript, Orval (cliente react-query), Ant Design, ESLint (última versión, flat config), Biome (formato y linting) |
| Backend | FastAPI |
| Worker | Servicios long-running que usan la librería `matriz-client` v0.3.0, instalada desde el wheel publicado en GitHub Releases (`gravity-quant/market-libs`) |
| Model | Modelos y servicios de BD compartidos por `backend` y `worker` (paquete propio o carpeta importable) |
| Python | `uv` con workspaces; Ruff (lint + `ruff format`); Pyright en modo `strict` |
| Persistencia | SQLAlchemy 2 con estilo tipado nativo (`DeclarativeBase`, `Mapped[]`, `mapped_column()`), sin plugins; PostgreSQL |
| Configuración | Un único `.env` / `.env.example` centralizado en la raíz |
| Ejecución | Modo dev por proyecto individual; modo producción con `docker-compose` |
| Testing | Unit tests por proyecto; integración con Playwright para Python |

## User Stories

- **US-1** — Como desarrollador, quiero que el repositorio sea un monorepo con `frontend/`, `backend/`, `worker/` y `model/`, configurado para que VS Code y Claude Code lo traten como tal, para navegar y trabajar en todas las partes desde un único workspace.
- **US-2** — Como desarrollador frontend, quiero una app Vite + React + React Router + TypeScript + Ant Design con un cliente Orval/react-query generado desde el backend, para consumir la API con tipos correctos.
- **US-3** — Como desarrollador backend, quiero un proyecto FastAPI que exponga los endpoints y el esquema OpenAPI que el frontend necesita, para tener una API funcional desde el día uno.
- **US-4** — Como desarrollador, quiero un proyecto `worker` con un proceso long-running que use `matriz-client`, para tener la base sobre la que construir la integración con Matriz.
  - Decisión del usuario: `matriz-client` se instala desde `https://github.com/gravity-quant/market-libs/releases/download/matriz-client-v0.3.0/matriz_client-0.3.0-py3-none-any.whl` (indicado originalmente como `uv pip install <url>`). Para que quede en `pyproject.toml` y `uv.lock` (AC-16, AC-22, AC-39) se declara como fuente URL del workspace (`uv add <url>` → `[tool.uv.sources]`), no con `uv pip install`, que no actualiza el lockfile.
- **US-5** — Como desarrollador, quiero un proyecto `model` con SQLAlchemy 2 tipado sobre PostgreSQL, importable por `backend` y `worker`, para compartir una única definición del modelo de datos.
- **US-6** — Como desarrollador Python, quiero que `backend`, `worker` y `model` usen `uv` workspaces, Ruff y Pyright strict, para tener dependencias reproducibles y código consistente y tipado.
- **US-7** — Como desarrollador, quiero un único `.env` / `.env.example` en la raíz, para configurar todas las partes desde un solo lugar.
- **US-8** — Como desarrollador, quiero correr cada proyecto individualmente en modo dev, para iterar rápido sobre una sola pieza.
- **US-9** — Como operador, quiero levantar todo el sistema en modo producción con `docker-compose`, para desplegarlo con un único comando.
- **US-10** — Como desarrollador, quiero unit tests configurados en cada proyecto, para validar cambios localmente.
- **US-11** — Como desarrollador, quiero tests de integración con Playwright para Python, para verificar el sistema de punta a punta.

## Acceptance Criteria (EARS)

### Monorepo (US-1)

- AC-1: WHEN se clona el repositorio THEN the system SHALL contener en la raíz los directorios `frontend/`, `backend/`, `worker/` y `model/`. (US-1)
- AC-2: WHEN se abre el repositorio en VS Code THEN the system SHALL proveer un archivo `*.code-workspace` (multi-root) que liste `frontend`, `backend`, `worker` y `model` como carpetas del workspace, y una configuración de VS Code que asigne Biome como formateador de TS/TSX y Ruff como formateador de Python. (US-1)
- AC-3: WHEN Claude Code se ejecuta en la raíz del repositorio THEN the system SHALL proveer un `CLAUDE.md` raíz que describa la estructura del monorepo y los comandos de dev/lint/test por proyecto, y un `CLAUDE.md` en cada uno de los cuatro proyectos con sus comandos específicos. (US-1)

### Frontend (US-2)

- AC-4: WHEN se ejecuta el comando de instalación de dependencias en `frontend/` THEN the system SHALL instalar Vite, React, React Router, TypeScript, Orval, `@tanstack/react-query`, Ant Design, ESLint (última versión mayor estable, con flat config `eslint.config.*`) y Biome, sin errores. (US-2)
- AC-5: WHEN se ejecuta el script `build` del frontend sobre un clon limpio, sin el backend en ejecución THEN the system SHALL completar `tsc` sin errores y producir el bundle de Vite con exit code 0. (US-2)
- AC-6: WHEN se ejecuta el script de generación de Orval THEN the system SHALL generar hooks de react-query tipados a partir del esquema OpenAPI del backend en un directorio dedicado de código generado. (US-2, US-3)
- AC-7: WHEN el usuario abre la ruta raíz `/` del frontend THEN the system SHALL renderizar, mediante React Router y componentes de Ant Design, una página que muestre los valores de `status` y `database` devueltos por `GET /health` (AC-10), obtenidos a través del hook generado por Orval. (US-2)
- AC-8: IF el backend no responde, devuelve HTTP 503 (AC-11) o cualquier otro error THEN the system SHALL mostrar en la página raíz, en menos de 15 segundos desde la carga, un estado de error visible (componente de Ant Design) en lugar de una pantalla en blanco o una excepción no capturada. (US-2)
- AC-45: WHILE la petición a `GET /health` está en curso THE system SHALL mostrar un indicador de carga de Ant Design en la página raíz. (US-2)
- AC-9: WHEN se ejecutan los scripts `lint` (ESLint y Biome) y `format:check` (Biome) del frontend THEN the system SHALL terminar con exit code 0 sobre el código inicial, excluyendo el código generado por Orval. (US-2)

### Backend (US-3)

- AC-10: WHEN el backend está en ejecución THEN the system SHALL exponer `GET /health` que responda, cuando PostgreSQL es alcanzable, HTTP 200 con un cuerpo JSON con los campos `status: "ok"` y `database: "ok"`, declarado como modelo de respuesta tipado en el esquema OpenAPI. (US-3)
- AC-11: IF PostgreSQL no es alcanzable THEN the system SHALL responder `GET /health` en menos de 5 segundos con HTTP 503 y un cuerpo JSON con el mismo esquema que AC-10 y `database: "unavailable"`. (US-3)
- AC-12: WHEN el backend está en ejecución THEN the system SHALL servir el esquema OpenAPI en `GET /openapi.json`, consumible por Orval. (US-3)
- AC-13: WHILE el backend corre en modo dev THE system SHALL aceptar peticiones CORS desde el origen del servidor dev del frontend, configurado vía `.env`. (US-3, US-8)
- AC-46: IF faltan variables de entorno obligatorias para el backend THEN the system SHALL no arrancar, terminar con exit code distinto de 0 y emitir un mensaje que nombre las variables faltantes. (US-3, US-7)

### Worker (US-4)

- AC-14: WHEN se inicia el worker THEN the system SHALL arrancar un proceso long-running que permanezca activo hasta recibir SIGINT o SIGTERM. (US-4)
- AC-15: WHEN el worker recibe SIGINT o SIGTERM THEN the system SHALL finalizar ordenadamente con exit code 0 en menos de 10 segundos. (US-4)
- AC-16: WHEN se ejecuta `uv sync` en la raíz THEN the system SHALL instalar `matriz-client` 0.3.0 desde la URL del wheel de GitHub Releases indicada en US-4, declarado en el `pyproject.toml` del worker (fuente URL en `[tool.uv.sources]`), fijado en `uv.lock` e importable sin errores. (US-4, US-6)
- AC-17: WHEN el worker arranca THEN the system SHALL inicializar un cliente de `matriz-client` con la configuración leída de `.env` y registrar en el log el resultado de la inicialización. (US-4)
- AC-18: IF faltan variables de entorno obligatorias para el worker THEN the system SHALL terminar con exit code distinto de 0 y un mensaje de log que nombre las variables faltantes. (US-4, US-7)

### Model (US-5)

- AC-19: WHEN se importa el paquete `model` desde `backend` o `worker` THEN the system SHALL exponer una clase base que herede de `DeclarativeBase` y un factory de sesión/engine de SQLAlchemy 2 configurado con la URL de PostgreSQL de `.env`. (US-5)
- AC-20: WHEN se define cualquier modelo en `model` THEN the system SHALL usar exclusivamente anotaciones `Mapped[]` y `mapped_column()`, sin plugins de SQLAlchemy ni de mypy. (US-5)
- AC-21: WHEN se inicia el sistema en cualquier modo THEN the system SHALL usar PostgreSQL como única base de datos, incluida en tests de integración. (US-5)

### Tooling Python (US-6)

- AC-22: WHEN se ejecuta `uv sync` en la raíz THEN the system SHALL resolver un único `uv.lock` para el workspace que incluya `backend`, `worker` y `model` como miembros. (US-6)
- AC-23: WHEN se ejecuta `ruff check` y `ruff format --check` en la raíz THEN the system SHALL terminar con exit code 0 sobre todo el código Python. (US-6)
- AC-24: WHEN se ejecuta Pyright en la raíz THEN the system SHALL analizar `backend`, `worker` y `model` con `typeCheckingMode = "strict"` y reportar 0 errores. (US-6)

### Configuración (US-7)

- AC-25: WHEN se clona el repositorio THEN the system SHALL contener un único `.env.example` en la raíz con todas las variables que usan `frontend`, `backend`, `worker`, `model` y `docker-compose`, cada una con un valor de ejemplo o comentario. (US-7)
- AC-26: WHEN cualquier proyecto se ejecuta en modo dev o producción THEN the system SHALL leer su configuración del `.env` de la raíz, sin archivos `.env` por proyecto. (US-7)
- AC-27: WHEN se versiona el repositorio THEN the system SHALL excluir `.env` vía `.gitignore` e incluir `.env.example`. (US-7)

### Modo dev (US-8)

- AC-28: WHEN se ejecuta el comando dev documentado de un proyecto (`frontend`, `backend` o `worker`) THEN the system SHALL arrancar solo ese proyecto, con recarga automática ante cambios de código en `frontend` y `backend`. (US-8)
- AC-29: WHEN un desarrollador necesita PostgreSQL en modo dev THEN the system SHALL permitir levantar únicamente el servicio de PostgreSQL vía `docker compose up postgres`, sin levantar los demás servicios, exponiendo su puerto al host según `.env` para que `backend` y `worker` en modo dev se conecten. (US-8)

### Modo producción (US-9)

- AC-30: WHEN se ejecuta `docker compose up --build` en la raíz con un `.env` válido THEN the system SHALL construir y levantar los servicios `frontend`, `backend`, `worker` y `postgres`. (US-9)
- AC-31: WHEN se ejecuta `docker compose up` con imágenes ya construidas THEN the system SHALL servir el frontend como build estático y la página raíz SHALL mostrar `status: "ok"` y `database: "ok"` (AC-7) dentro de los 120 segundos posteriores al comando (el tiempo de build queda excluido). (US-9)
- AC-32: WHILE PostgreSQL no esté listo THE system SHALL demorar el arranque de `backend` y `worker` mediante un healthcheck de `postgres` y `depends_on: condition: service_healthy`. (US-9)
- AC-33: WHEN se ejecuta `docker compose down` (sin `-v`) seguido de `docker compose up` THEN the system SHALL conservar los datos de PostgreSQL, almacenados en un volumen nombrado. (US-9)

### Unit tests (US-10)

- AC-34: WHEN se ejecuta `pytest` en `backend`, `worker` o `model` THEN the system SHALL ejecutar al menos un unit test por proyecto y terminar con exit code 0. (US-10)
- AC-35: WHEN se ejecuta el script `test` del frontend THEN the system SHALL ejecutar al menos un unit test de componente con un runner integrado con Vite y terminar con exit code 0. (US-10)
- AC-36: WHEN se ejecutan los unit tests THEN the system SHALL no requerir PostgreSQL, Docker ni acceso a red a servicios de Matriz. (US-10)

### Integración (US-11)

- AC-37: WHEN se ejecuta la suite de integración con `pytest` + Playwright (Python) contra el sistema levantado THEN the system SHALL abrir la página raíz del frontend en un navegador headless y verificar que muestra el estado OK del backend (AC-7). (US-11)
- AC-38: WHEN se ejecuta la suite de integración THEN the system SHALL leer la URL base del frontend desde configuración (`.env` o variable de entorno) y terminar con exit code 0 si todos los tests pasan, o distinto de 0 si alguno falla. (US-11)

## Out of Scope

- Funcionalidad de negocio de trading, pantallas reales, autenticación y autorización.
- Modelos de dominio concretos y su lógica (solo se entrega la base `DeclarativeBase` y la sesión).
- Lógica real de integración con Matriz más allá de inicializar `matriz-client` (AC-17).
- Pipelines de CI/CD, despliegue a un entorno remoto, TLS/reverse proxy de producción, observabilidad y monitoreo.
- Hardening de seguridad de imágenes Docker y gestión de secretos fuera de `.env`.
- Decidir si `model` es un paquete publicable: en este ticket es un miembro del workspace `uv` importable por `backend` y `worker`.

## Non-Functional Requirements

### NFR-1 — Reproducibilidad

- AC-39: WHEN se versiona el repositorio THEN the system SHALL incluir lockfiles versionados (`uv.lock` y el lockfile del gestor de paquetes del frontend) que fijen todas las dependencias. (US-2, US-6)

### NFR-2 — Versiones

- AC-40: WHEN se construyen las imágenes Docker THEN the system SHALL usar las mismas versiones de Python y Node que las fijadas en archivos del repositorio (p. ej. `.python-version`, `engines`/`.nvmrc`). (US-2, US-6, US-9)

### NFR-3 — Calidad

- AC-41: WHEN se ejecutan lint, formato, type-check y unit tests de todos los proyectos sobre el estado inicial del repositorio THEN the system SHALL terminar cada uno con exit code 0. (US-2, US-6, US-10)

### NFR-4 — Documentación

- AC-42: WHEN se clona el repositorio THEN the system SHALL contener un `README.md` raíz que documente requisitos previos, setup, comandos dev por proyecto, `docker compose` y ejecución de tests. (US-1, US-8, US-9)

### NFR-5 — Tiempo de arranque

- AC-43: WHEN se ejecuta `docker compose up` en modo producción con imágenes ya construidas THEN the system SHALL reportar `postgres`, `backend` y `frontend` como `healthy` (cada uno con un `healthcheck` definido en Compose) y `worker` como `running` sin reinicios, en menos de 120 segundos. (US-9)

### NFR-6 — Secretos

- AC-44: WHEN se versiona el repositorio THEN the system SHALL no incluir ningún secreto real y SHALL limitar `.env.example` a valores de ejemplo. (US-7)

## Open Questions
- [x] ¿De dónde se instala `matriz-client` y cómo se declara en el workspace `uv`? — **Resolved:** **Resuelto (US-4, AC-16):** se instala desde el wheel `matriz_client-0.3.0-py3-none-any.whl` de GitHub Releases de `gravity-quant/market-libs` y se declara como fuente URL en `[tool.uv.sources]`.

Es la decisión explícita del usuario y, a diferencia de `uv pip install`, queda registrada en `pyproject.toml` y `uv.lock`, como exigen AC-16, AC-22 y AC-39.
  - **Resuelto (US-4, AC-16):** desde el wheel `matriz_client-0.3.0-py3-none-any.whl` de GitHub Releases de `gravity-quant/market-libs`, declarado como fuente URL en `[tool.uv.sources]`.
- [x] ¿El repositorio `gravity-quant/market-libs` es público? Si es privado, `uv sync` local y el build de Docker necesitan un token de GitHub; hay que definir cómo se inyecta (variable de `.env`, build secret de Docker) sin violar AC-44. — **Resolved:** 🔧 **Bash**

```bash
curl -sI -o /dev/null -w "%{http_code}\n" https://github.com/gravity-quant/market-libs; curl -sIL -o /dev/null -w "%{http_code}\n" https://github.com/gravity-quant/market-libs/releases/download/matriz-client-v0.3.0/matriz_client-0.3.0-py3-none-any.whl
```This Bash command contains multiple operations. The following parts require approval: curl -sI -o /dev/null -w "%{http_code}\n" https://github.com/gravity-quant/market-libs, curl -sIL -o /dev/null -w "%{http_code}\n" https://github.com/gravity-quant/market-libs/releases/download/matriz-client-v0.3.0/matriz_client-0.3.0-py3-none-any.whlAntes de implementar, confirmen con `curl -sIL <url-del-wheel>` sin credenciales si el repo es público; no pude comprobarlo porque la petición no fue aprobada. Si responde 200, se usa la URL tal cual en `[tool.uv.sources]` y no hace falta configurar nada más. Si es privado, la URL de `pyproject.toml` y `uv.lock` se deja sin credenciales y el token se pasa solo al ejecutar: en local, un `GITHUB_TOKEN` (fine-grained, solo lectura de contents de `gravity-quant/market-libs`) en `~/.netrc` o en el `.env`, con un placeholder vacío en `.env.example`. En Docker se pasa con `RUN --mount=type=secret,id=github_token` y `secrets:` en `docker-compose.yml`, nunca como `ARG`/`ENV`, para que no quede en las capas de la imagen. Así se cumple AC-44 y el lockfile sigue siendo reproducible (AC-39). El README (AC-42) debe documentar cómo crear el token y que `uv sync` y `docker compose build` fallan sin él.
- [x] ¿Qué variables de entorno o credenciales requiere `matriz-client` para inicializarse (AC-17, AC-18, AC-25)? — **Resolved:** Las variables se toman de la firma del constructor y de la configuración pública de `matriz-client` 0.3.0. Antes de implementar AC-17 hay que revisar el wheel y confirmar los nombres. Se declaran con el prefijo `MATRIZ_`: como mínimo `MATRIZ_BASE_URL` (o el host/entorno equivalente que pida el cliente), `MATRIZ_USERNAME`, `MATRIZ_PASSWORD` y, si la librería lo requiere, `MATRIZ_ACCOUNT`. El worker las valida al arrancar con un modelo de `pydantic-settings` que lee el `.env` de la raíz (AC-26). Si falta alguna obligatoria, el worker termina con un exit code distinto de 0 y un log que nombra las variables faltantes (AC-18). En `.env.example` van solo valores de ejemplo, como `changeme` o la URL del entorno de pruebas, para cumplir AC-25 y AC-44. Los unit tests usan un cliente simulado y valores ficticios, sin credenciales reales (AC-36).
- [x] Al arrancar, ¿el worker debe conectarse realmente a Matriz o alcanza con instanciar el cliente (AC-17)? — **Resolved:** Conectarse de verdad y terminar con exit code distinto de 0 si falla — falla rápido, pero en Docker cae en un bucle de reinicios si Matriz no responde
  - Conectarse de verdad y terminar con exit code distinto de 0 si falla — falla rápido, pero en Docker cae en un bucle de reinicios si Matriz no responde
  - Solo instanciar el cliente y registrar el resultado — no depende de la disponibilidad de Matriz, pero no verifica conectividad real
- [x] ¿El código generado por Orval se versiona en el repo? AC-5 exige que `build` funcione sin el backend en ejecución. — **Resolved:** Versionar el código generado — el build (incluido Docker) no depende del backend, pero hay que regenerarlo y commitearlo al cambiar la API
  - Versionar el código generado — el build (incluido Docker) no depende del backend, pero hay que regenerarlo y commitearlo al cambiar la API
  - Versionar un `openapi.json` exportado del backend y generar en el build — el código generado queda fuera del repo, pero suma un paso de exportación
- [x] ¿Se incluyen las migraciones de base de datos con Alembic en este ticket? — **Resolved:** Sí, configurado pero sin ejecución automática en Compose — es más simple, pero las migraciones quedan como paso manual
  - Sí, configurado pero sin ejecución automática en Compose — es más simple, pero las migraciones quedan como paso manual
  - No, queda fuera de alcance — es el ticket más chico, pero el primer modelo real tendrá que agregarlo
- [ ] ¿Cómo se sirve el frontend en producción y cómo llega al backend?
  - nginx en el servicio `frontend` sirve el build estático y hace proxy de `/api` a `backend` — mismo origen, sin CORS en producción y coherente con AC-30, pero suma la configuración de nginx
  - FastAPI sirve el build estático (`StaticFiles`) — se elimina un contenedor, pero se mezclan responsabilidades y se contradice el servicio `frontend` de AC-30
- [x] ¿Qué gestor de paquetes usa el frontend? — **Resolved:** npm — no requiere nada extra y es lo más compatible, pero es más lento y menos estricto
  - pnpm — es rápido y estricto con las dependencias, pero en Docker requiere `corepack`
  - npm — no requiere nada extra y es lo más compatible, pero es más lento y menos estricto
  - bun — es el más rápido, pero tiene menor madurez de ecosistema y puede no coincidir con `engines`/`.nvmrc`
- [x] ¿Dónde viven los tests de integración con Playwright? — **Resolved:** En un directorio raíz `e2e/` como miembro propio del workspace `uv` — separa las dependencias de navegador de los servicios, a cambio de un quinto proyecto
  - En un directorio raíz `e2e/` como miembro propio del workspace `uv` — separa las dependencias de navegador de los servicios, a cambio de un quinto proyecto
  - En `backend/tests/integration` — se evita un proyecto más, pero Playwright y los navegadores se cuelan en la imagen o en las dependencias del backend
  - En `e2e/` fuera del workspace, con su propio `pyproject` — queda aislado, pero tiene un lockfile aparte y rompe AC-22
- [ ] **ESLint + Biome**: ambos hacen linting. ¿Qué responsabilidad tiene cada uno? Propuesta: Biome para formato y reglas generales; ESLint solo para reglas que Biome no cubre (p. ej. `react-hooks`, `react-refresh`), con las reglas solapadas desactivadas.
- [ ] **Runner de unit tests del frontend**: no fue especificado. Propuesta: Vitest + Testing Library (AC-35).
- [ ] **Versiones**: ¿Python 3.12 o 3.13? ¿Node 22 LTS o 24 LTS? (AC-40)
- [ ] **"vsclaude"**: se interpretó como VS Code + Claude Code (AC-2, AC-3). Confirmar.
- [x] ¿Cómo se resuelve que el `build` del frontend funcione sin el backend en ejecución (código generado por Orval)? — **Resolved:** Versionar un `openapi.json` exportado del backend y generar el cliente en el build — el código generado no entra al repo, pero suma un script de exportación
  - Versionar un `openapi.json` exportado del backend y generar el cliente en el build — el código generado no entra al repo, pero suma un script de exportación
  - Versionar el código generado por Orval — el build y Docker no dependen de nada, pero hay que regenerarlo y commitearlo en cada cambio de API
  - Generar desde el backend en vivo durante el build de Docker — no hay artefactos versionados, pero se rompe AC-5 y el build queda acoplado al backend
- [ ] Al arrancar, ¿el worker debe conectarse realmente a Matriz o alcanza con instanciar `matriz-client`?
  - Solo instanciar el cliente y registrar el resultado — no depende de Matriz y AC-43 (sin reinicios) es alcanzable, pero no verifica la conectividad real
  - Conectarse y reintentar con backoff sin terminar el proceso — verifica la conectividad sin caer en bucles de reinicio, pero agrega lógica de reintentos
  - Conectarse y salir con exit code distinto de 0 si falla — falla rápido, pero en Docker entra en un bucle de reinicios que viola AC-43
- [ ] ¿Se incluye Alembic para migraciones en este ticket?
  - Sí, configurado en `model` con una migración inicial vacía y ejecución manual — la base queda lista para el primer modelo, sin acoplar el arranque de Compose
  - No, queda fuera de alcance — es el ticket más chico, pero el primer modelo real tendrá que configurarlo

## Solicitud original

> Texto original del usuario, preservado como referencia.

Quiero realizar el setup inicial del proyecto Matriz Trader.

Requerimientos:

Quiero que el proyecto este estructurado como un monorepo por lo cual quiero que se agregue la configuracion necesaria para que vsclaude y claude lo traten como tal.

El monorepo debe tener las siguientes partes:

frontend:

Debe utilizar: vite, react, react-router, typescript, orval (en su variante con react-query, para el acceso al backend), Ant Design para los componentes de Frontend, Eslint en su ultima verison (buscar la mejor var) y Biome para formateo y linting.

bakend:

Contendra un proyecto fast-api que servira los endpoints necesarios para que el frontend pueda funcionar.

worker:

Contendra los servicios long running interactuara con los servicios de matriz utilizando la libreria matriz-client.

model:

Contendra los modelos y servicios necesarios para que el backend y worker puedan interactuar con la base de datos. Esta carpeta puede ser un packete en si mismo o simplemente un folder del que model y worker importen dependiendo de como avance el proyecto

Para el backend, worker y model utilizaremos uv para gestionar los entornos virtuales y las dependencias mediante workspaces. Ruff se usará como linter y también como formateador, con ruff format. El tipado estricto se verificará con Pyright en modo strict. Para la persistencia usaremos SQLAlchemy 2, definiendo todos los modelos con el estilo tipado nativo (DeclarativeBase, Mapped[] y mapped_column()), sin plugins adicionales.

la base de datos debe ser PostgreSQL.

Para la configuracion de las variables de entorno quiero utilizar un unico archivo .env / .env.example centralizado

Quiero poder correr los proyectos en modo dev individualmente o en modo produccion con docker-compose

En este ticket solo quiero hacer la inicializacio del proyecto. No tengo otros requerimientos especiales por fuera de que cada pieza funcione correctamente.

Quiero tambien seteados los mecanismos de unit test necesarios.

El proyecto utilizara Playwight con python para las pruebas de integracion

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿De dónde se instala `matriz-client` y cómo se declara en el workspace `uv`?** — **Resuelto (US-4, AC-16):** se instala desde el wheel `matriz_client-0.3.0-py3-none-any.whl` de GitHub Releases de `gravity-quant/market-libs` y se declara como fuente URL en `[tool.uv.sources]`.
- **¿El repositorio `gravity-quant/market-libs` es público? Si es privado, `uv sync` local y el build de Docker necesitan un token de GitHub; hay que definir cómo se inyecta (variable de `.env`, build secret de Docker) sin violar AC-44.** — 🔧 **Bash**
- **¿Qué variables de entorno o credenciales requiere `matriz-client` para inicializarse (AC-17, AC-18, AC-25)?** — Las variables se toman de la firma del constructor y de la configuración pública de `matriz-client` 0.3.0. Antes de implementar AC-17 hay que revisar el wheel y confirmar los nombres. Se declaran con el prefijo `MATRIZ_`: como mínimo `MATRIZ_BASE_URL` (o el host/entorno equivalente que pida el cliente), `MATRIZ_USERNAME`, `MATRIZ_PASSWORD` y, si la librería lo requiere, `MATRIZ_ACCOUNT`. El worker las valida al arrancar con un modelo de `pydantic-settings` que lee el `.env` de la raíz (AC-26). Si falta alguna obligatoria, el worker termina con un exit code distinto de 0 y un log que nombra las variables faltantes (AC-18). En `.env.example` van solo valores de ejemplo, como `changeme` o la URL del entorno de pruebas, para cumplir AC-25 y AC-44. Los unit tests usan un cliente simulado y valores ficticios, sin credenciales reales (AC-36).
- **Al arrancar, ¿el worker debe conectarse realmente a Matriz o alcanza con instanciar el cliente (AC-17)?** — Conectarse de verdad y terminar con exit code distinto de 0 si falla — falla rápido, pero en Docker cae en un bucle de reinicios si Matriz no responde
- **¿El código generado por Orval se versiona en el repo? AC-5 exige que `build` funcione sin el backend en ejecución.** — Versionar el código generado — el build (incluido Docker) no depende del backend, pero hay que regenerarlo y commitearlo al cambiar la API
- **¿Se incluyen las migraciones de base de datos con Alembic en este ticket?** — Sí, configurado pero sin ejecución automática en Compose — es más simple, pero las migraciones quedan como paso manual
- **¿Qué gestor de paquetes usa el frontend?** — npm — no requiere nada extra y es lo más compatible, pero es más lento y menos estricto
- **¿Dónde viven los tests de integración con Playwright?** — En un directorio raíz `e2e/` como miembro propio del workspace `uv` — separa las dependencias de navegador de los servicios, a cambio de un quinto proyecto
- **¿Cómo se resuelve que el `build` del frontend funcione sin el backend en ejecución (código generado por Orval)?** — Versionar un `openapi.json` exportado del backend y generar el cliente en el build — el código generado no entra al repo, pero suma un script de exportación
