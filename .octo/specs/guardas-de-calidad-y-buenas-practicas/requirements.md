# Requirements: Guardas de calidad y buenas prácticas (backend, frontend y agentes)

## Introduction

`matriz-trader` va a ser un cliente de trading **manual asistido y algorítmico** sobre Matriz, construido con `market-data-client` y `matriz-client`. Hoy es un esqueleto (solo `GET /api/health`) y la mayor parte del código nuevo la van a escribir **agentes de IA** (Claude Code y Octo), con personas revisando. Los agentes cumplen lo que se verifica de forma automática, pero no siempre lo que solo está escrito. Este spec convierte las buenas prácticas en **gates ejecutables** antes de que empiece el desarrollo de funcionalidades.

### Problem statement

Las convenciones del proyecto están **documentadas** en `CLAUDE.md`, pero casi ninguna se **verifica de forma automática**:

1. **Sin gate obligatorio.** No hay CI (`.github/` no existe), ni hooks de git, ni protección de `main`. La «Definición de terminado» (§9 de `CLAUDE.md`) depende de que quien hace el cambio, persona o agente, recuerde correr ocho comandos y lea su salida.
2. **Arquitectura del frontend sin verificar.** Hay reglas que ninguna herramienta verifica: las de dependencia entre carpetas (§3: una pantalla no importa de otra, `components/` no importa `api/generated`, `utils/` no usa React, nada de `../../`) y las prohibiciones de §5 y §7 (`fetch` fuera de `src/api/mutator.ts`, `any`, `!`, `console.log`, `enum`, `dangerouslySetInnerHTML`). `frontend/vite.config.ts` activa solo 3 reglas de Oxlint.
3. **Backend sin capas.** No hay separación api → servicios → datos, ni herramienta que la imponga. Tampoco hay Alembic, logging estructurado ni un formato de error estándar que Orval pueda tipar. Ruff activa 10 grupos de reglas y deja afuera async, seguridad, fechas con zona horaria y FastAPI.
4. **Sin reglas de dominio.** En un cliente que **envía órdenes reales**, nada impide usar `float` para un precio o un `datetime` sin zona horaria, y nada fija cómo se va a evitar una orden duplicada o cómo se detiene el envío (kill switch). En este dominio cada uno de esos errores cuesta dinero.
5. **Seguridad y supply chain sin cubrir.** No se detectan secretos, no se auditan dependencias, no se actualizan automáticamente y no se revisan los workflows.
6. **La capa de agentes está rota o vacía.**
   - El hook de Octo `.octo/hooks/code-validate-improve.json` corre `npm run typecheck`, un comando que no existe en este repo.
   - `.octo/steering/{product,tech,structure}.md` están vacíos.
   - No hay hooks de Claude Code que validen las ediciones del agente ni que impidan tocar código generado.

### Objetivo

Que **las mismas verificaciones** corran, con los **mismos scripts**, en tres momentos: cuando un agente edita o termina un turno, cuando alguien commitea y cuando se abre un PR. Todas son **bloqueantes desde el día 1** y usan **solo herramientas OSS o gratuitas**. El esqueleto actual es el mejor momento para activarlas: hoy pasar todos los gates no cuesta nada, y más adelante cada regla nueva implicaría arreglar deuda acumulada.

Notas de formato:
- Las palabras clave de las historias (`As a`, `I want`, `so that`) y de EARS (`WHEN`, `WHILE`, `IF`, `THEN`, `the system SHALL`) quedan en inglés porque Octo las parsea literalmente.
- «El sistema» es el repositorio con sus herramientas, scripts, hooks y workflows.
- «Gate de un módulo» es el script único que ejecuta los comandos de §9 de `CLAUDE.md` para `backend/` o `frontend/`.

## User Stories

- US-1: As a mantenedor del repo, I want un pipeline de CI en GitHub Actions que corra todos los gates en cada PR y bloquee el merge a `main` si alguno falla, so that ningún cambio, de una persona o de un agente, llegue a `main` sin pasar la Definición de terminado.
- US-2: As a desarrollador, I want hooks de git locales que formateen, linteen y validen el mensaje de commit antes de commitear, so that los errores aparezcan en segundos y no en CI.
- US-3: As a mantenedor que delega el desarrollo en agentes de IA, I want hooks de Claude Code y de Octo que bloqueen la edición de archivos protegidos, validen cada archivo editado y corran el gate del módulo antes de que el agente dé el trabajo por terminado, so that el agente corrija sus propios errores sin intervención humana.
- US-4: As a desarrollador backend, I want que las capas del backend (rutas, servicios, datos y dominio) estén definidas y verificadas por una herramienta, so that la lógica de negocio no termine acoplada a FastAPI o a SQLAlchemy.
- US-5: As a desarrollador frontend, I want que las reglas de dependencia entre carpetas y las prohibiciones de `CLAUDE.md` sean errores de lint, so that una violación de arquitectura rompa `vp check` en vez de depender de la revisión.
- US-6: As a desarrollador, I want reglas de Ruff y opciones de TypeScript más estrictas, orientadas a async, seguridad, fechas y FastAPI, so that los errores típicos de esas tecnologías se detecten en el análisis estático.
- US-7: As a mantenedor, I want umbrales de cobertura y tests de propiedades, de contrato, de integración con PostgreSQL y de accesibilidad, so that la suite de tests mida el comportamiento y no solo que el código ejecute.
- US-8: As a desarrollador backend, I want Alembic configurado con detección de drift y lint de migraciones, so that ninguna migración insegura o faltante llegue a la base de datos.
- US-9: As a mantenedor, I want detección de secretos, auditoría de dependencias, actualizaciones automáticas y análisis de seguridad de los workflows, so that el repo no filtre credenciales del broker ni incorpore dependencias vulnerables.
- US-10: As a operador del sistema de trading, I want logs estructurados con un ID de correlación por request y errores en formato estándar, so that pueda seguir una orden de punta a punta y el frontend muestre errores tipados.
- US-11: As a trader que usa el sistema en modo manual o algorítmico, I want reglas de dominio verificables sobre precisión numérica, tiempo, idempotencia y controles de riesgo, so that un error de software no se convierta en una orden incorrecta o duplicada.
- US-12: As a agente de IA o desarrollador que se suma al proyecto, I want steering de Octo completo, `CLAUDE.md` dividido por módulo y una plantilla de PR con la checklist, so that el contexto que recibo sea corto, específico de la carpeta y coherente con lo que verifican las herramientas.

## Acceptance Criteria (EARS notation)

- AC-1: WHEN se abre o actualiza un PR contra `main` THEN the system SHALL ejecutar `.github/workflows/ci.yml` con los jobs `backend`, `frontend`, `e2e`, `migrations`, `security` y `workflow-lint`, y un job agregador `ci-ok` que termina con éxito solo si ninguno de esos jobs falló. (US-1)
- AC-2: WHEN un PR modifica archivos solo dentro de `frontend/` THEN the system SHALL omitir el job `backend` mediante un filtro de rutas por job (`dorny/paths-filter` o equivalente), y `ci-ok` SHALL reportar éxito sin quedar pendiente. (US-1)
- AC-3: WHEN se inspecciona cualquier workflow en `.github/workflows/` THEN the system SHALL declarar `permissions: {}` a nivel de workflow, otorgar permisos mínimos por job y fijar cada acción de terceros por SHA de commit completo. (US-1, US-9)
- AC-4: WHEN el job `backend` instala dependencias THEN the system SHALL obtener `market-libs` mediante un token de GitHub App o PAT, guardado como secret de Actions, reescribiendo `ssh://git@github.com/` a HTTPS con `git config url.<base>.insteadOf`, sin escribir el token en logs ni en archivos versionados. (US-1)
- AC-5: IF el secret de acceso a `market-libs` no está definido THEN the system SHALL hacer fallar el job `backend` con un mensaje que nombre el secret faltante. (US-1)
- AC-6: WHEN los jobs `backend` y `frontend` se ejecutan por segunda vez sin cambios en `uv.lock` ni en `pnpm-lock.yaml` THEN the system SHALL restaurar las dependencias desde la caché de Actions. (US-1)
- AC-7: WHEN se inspecciona `README.md` THEN the system SHALL documentar el ruleset de `main` (PR obligatorio, check `ci-ok` requerido, rama actualizada y sin force-push), el secret que necesita el CI y el comando `gh api` para aplicar el ruleset. (US-1, US-12)
- AC-8: WHEN se ejecuta `lefthook install` en la raíz THEN the system SHALL instalar los hooks `pre-commit` y `commit-msg` definidos en un único `lefthook.yml` en la raíz del repo. (US-2)
- AC-9: WHEN se commitean archivos `.py` de `backend/` THEN the system SHALL ejecutar `ruff format`, `ruff check --fix` y `mypy` desde `backend/`, volver a stagear los archivos corregidos y abortar el commit si queda algún error. (US-2)
- AC-10: WHEN se commitean archivos `.ts` o `.tsx` de `frontend/` THEN the system SHALL ejecutar `vp check --fix` y la verificación de arquitectura (`vp run lint:arch`) desde `frontend/`, y abortar el commit si queda algún error. (US-2)
- AC-11: IF un commit incluye cambios en `frontend/src/api/generated/` sin cambios en `backend/openapi.json` THEN the system SHALL abortar el commit con un mensaje que explique el flujo de §5 de `CLAUDE.md`. (US-2)
- AC-12: IF un commit incluye un secreto detectable por gitleaks THEN the system SHALL abortar el commit e indicar archivo y línea. (US-2, US-9)
- AC-13: IF el mensaje de commit no cumple el formato `<tipo>(<scope>)?: <descripción>` con tipo en `feat|fix|chore|docs|refactor|test|perf|ci|build` y primera línea de hasta 72 caracteres THEN the system SHALL abortar el commit con un mensaje que muestre el formato esperado. (US-2)
- AC-14: IF un agente de Claude Code intenta editar o escribir un archivo en `frontend/src/api/generated/`, `backend/openapi.json`, `.env`, `backend/uv.lock` o `frontend/pnpm-lock.yaml` THEN the system SHALL bloquear la herramienta con un hook `PreToolUse` (exit 2) e indicar el comando que regenera ese archivo. (US-3)
- AC-15: WHEN un agente de Claude Code edita o escribe un archivo `.py`, `.ts` o `.tsx` THEN the system SHALL formatear y lintear ese archivo con un hook `PostToolUse` y, si queda algún error, devolverlo al agente por stderr con exit 2. (US-3)
- AC-16: WHEN un agente de Claude Code intenta terminar su turno con cambios sin commitear en `backend/` o `frontend/` THEN the system SHALL ejecutar con un hook `Stop` el gate de cada módulo modificado y, si falla, impedir que el turno termine (exit 2) y devolver la salida del gate. (US-3)
- AC-17: IF el hook `Stop` recibe `stop_hook_active: true` THEN the system SHALL terminar con exit 0 sin volver a ejecutar el gate. (US-3)
- AC-18: WHEN se inspecciona `.octo/hooks/code-validate-improve.json` THEN the system SHALL invocar el mismo script de gate que usan el hook `Stop`, `lefthook` y CI, y SHALL no hacer referencia a `npm`. (US-3)
- AC-19: WHEN se ejecuta el gate de un módulo desde CI, desde `lefthook`, desde el hook `Stop`, desde el hook de Octo o a mano THEN the system SHALL invocar el único script versionado `scripts/gate.sh` con el módulo y el modo (`quick` o `full`) como argumentos, y ningún otro archivo SHALL repetir la lista de comandos de un gate. (US-1, US-2, US-3)
- AC-20: WHEN se ejecuta `uv run lint-imports` desde `backend/` THEN the system SHALL verificar con import-linter un contrato de capas `app.scripts` → `app.main` → `app.api` → `app.services` → `app.db | app.schemas` → `app.domain` → `app.core`, y terminar con código 0 sobre el esqueleto. (US-4)
- AC-21: IF un módulo de `app.domain` importa `fastapi`, `sqlalchemy`, `httpx` o `matriz_client` THEN the system SHALL hacer fallar `uv run lint-imports` nombrando el import prohibido. (US-4, US-11)
- AC-22: IF un módulo de `app.api` importa modelos de `app.db` o `sqlalchemy` de forma directa, salvo la dependencia de sesión declarada como excepción, THEN the system SHALL hacer fallar `uv run lint-imports`. (US-4)
- AC-23: WHEN se inspecciona la configuración de Ruff THEN the system SHALL tener activos, además de los actuales, los grupos `ASYNC`, las reglas de FastAPI (`FAST001`, `FAST002`, `FAST003`), `S`, `DTZ`, `BLE`, `TRY`, `T20`, `ERA`, `PT`, `PIE`, `RET`, `C4`, `PTH`, `LOG`, `G`, `PERF`, `TC`, `ARG`, `FURB`, `TID`, `PL`, `C90` y `FBT`, con cada regla ignorada listada junto a un comentario que justifique la excepción. (US-6)
- AC-24: IF el código del backend usa `datetime.utcnow`, `datetime.now()` sin zona horaria, `time.sleep` dentro de `async def` o importa `requests` THEN the system SHALL hacer fallar `uv run ruff check .` con la regla correspondiente. (US-6, US-11)
- AC-25: WHEN se ejecuta `uv run pytest` THEN the system SHALL verificar en `tests/test_tooling.py` que los grupos de Ruff de AC-23 y los contratos de import-linter de AC-20 siguen activos, y fallar si alguno fue removido. (US-4, US-6)
- AC-26: WHEN se inspecciona el bloque `lint` de `frontend/vite.config.ts` THEN the system SHALL tener las categorías `correctness` y `suspicious` en `error`, los plugins `react`, `typescript`, `oxc`, `jsx-a11y`, `import`, `vitest`, `promise` y `unicorn`, y las reglas `typescript/no-explicit-any`, `typescript/no-non-null-assertion`, `typescript/no-floating-promises`, `react/no-danger`, `no-console` e `import/no-cycle` en `error`. (US-5)
- AC-27: IF un archivo de `frontend/src/` distinto de `src/api/mutator.ts` usa `fetch` o importa `axios` THEN the system SHALL hacer fallar `vp check` con un mensaje que remita al cliente Orval. (US-5)
- AC-28: IF un archivo de `frontend/src/` declara un `enum` o usa un import relativo que sube más de un nivel THEN the system SHALL hacer fallar `vp check`. (US-5)
- AC-29: WHEN se ejecuta `vp run lint:arch` desde `frontend/` THEN the system SHALL verificar con dependency-cruiser, sobre rutas resueltas (incluido el alias `@/`), que no haya ciclos, que ninguna pantalla importe de otra pantalla, que `components/` no importe de `screens/`, `api/`, `stores/` ni `layouts/`, que `hooks/` no importe de `screens/`, `components/` ni `layouts/`, que `utils/` y `constants/` solo importen de `types/` y que nadie importe archivos internos de una pantalla sin pasar por su `index.ts`. (US-5)
- AC-30: IF se introduce una violación de cualquiera de las reglas de AC-29 THEN the system SHALL hacer fallar `vp run lint:arch` con el nombre de la regla y los dos archivos involucrados. (US-5)
- AC-31: WHEN se ejecuta `vp run lint:unused` desde `frontend/` THEN the system SHALL informar con knip los archivos, exports y dependencias sin usar, excluyendo `src/api/generated/**`, y terminar con código distinto de 0 si encuentra alguno. (US-5)
- AC-32: WHEN se inspecciona `frontend/tsconfig*.json` THEN the system SHALL tener activos, además de los actuales, `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, `verbatimModuleSyntax`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noUnusedLocals` y `noUnusedParameters`. (US-6)
- AC-33: WHEN se ejecuta `uv run pytest` THEN the system SHALL medir la cobertura de branches de `app/` con pytest-cov y fallar si queda por debajo del umbral configurado en `[tool.coverage.report] fail_under`, y SHALL ejecutar los tests en orden aleatorio con pytest-randomly y tratar los warnings como errores. (US-7)
- AC-34: WHEN se ejecuta `uv run pytest` THEN the system SHALL correr Schemathesis contra la app ASGI usando el `openapi.json` versionado y fallar si alguna respuesta no cumple el esquema declarado. (US-7)
- AC-35: WHEN se ejecuta `uv run pytest -m db` con Docker disponible THEN the system SHALL levantar PostgreSQL 17 con testcontainers y ejecutar los tests marcados con `db` contra esa instancia. (US-7, US-8)
- AC-36: WHEN se ejecuta `vp test run --coverage` desde `frontend/` THEN the system SHALL medir la cobertura con el proveedor v8, excluir `src/api/generated/**`, `src/test/**` y `e2e/**`, y fallar si la cobertura de líneas o de branches queda por debajo de los umbrales de `test.coverage.thresholds` en `vite.config.ts`. (US-7)
- AC-37: WHEN se ejecuta `vp run e2e` THEN the system SHALL analizar con `@axe-core/playwright` las pantallas Home y 404 con las etiquetas `wcag2a`, `wcag2aa`, `wcag21aa` y `wcag22aa`, y fallar si se reporta al menos una violación. (US-7)
- AC-38: WHILE `CI` está definido en el entorno THE system SHALL ejecutar Playwright con `forbidOnly: true`, `retries: 2` y `trace: "on-first-retry"`, y publicar el trace como artefacto cuando un test falla. (US-7)
- AC-39: WHEN el job `frontend` ejecuta `vp build` THEN the system SHALL verificar con size-limit que el JavaScript comprimido con gzip de `dist/assets/` no supere el presupuesto versionado en el repo, y fallar indicando el tamaño medido y el límite. (US-7)
- AC-40: WHEN se inspecciona `backend/` THEN the system SHALL contener una configuración de Alembic creada con la plantilla async, con `target_metadata = Base.metadata` de `app.db.base` y la URL tomada de `Settings`. (US-8)
- AC-41: WHEN se ejecuta el job `migrations` THEN the system SHALL aplicar `alembic upgrade head` sobre un PostgreSQL 17 vacío y ejecutar `alembic check`, y fallar si los modelos ORM tienen cambios sin migración. (US-8)
- AC-42: WHEN se ejecuta el job `migrations` THEN the system SHALL generar el SQL de las migraciones con `alembic upgrade --sql` y analizarlo con Squawk, fallando ante operaciones que bloqueen tablas o no sean seguras para PostgreSQL. (US-8)
- AC-43: WHEN se ejecuta el job `security` THEN the system SHALL ejecutar gitleaks sobre el historial del PR, la auditoría de vulnerabilidades de las dependencias de Python (`uv audit` o `pip-audit` sobre `uv export --frozen`) y las de Node (OSV-Scanner sobre `pnpm-lock.yaml`), y fallar ante cualquier hallazgo que no figure en una allowlist versionada con justificación y fecha de vencimiento. (US-9)
- AC-44: WHEN se ejecuta el job `workflow-lint` THEN the system SHALL ejecutar actionlint y zizmor sobre `.github/workflows/`, y fallar ante cualquier hallazgo. (US-9)
- AC-45: WHEN se inspecciona la raíz del repo THEN the system SHALL contener una configuración de Renovate que agrupe las actualizaciones por módulo, aplique `minimumReleaseAge` de 7 días, actualice las acciones de GitHub fijadas por SHA y siga los tags de `market-data-client` y `matriz-client` en `gravity-quant/market-libs`. (US-9)
- AC-46: WHEN el backend recibe un request THEN the system SHALL registrar un log estructurado con structlog (JSON con `APP_ENV=production`, formato de consola en otro caso) que incluya un `correlation_id`, y SHALL devolver ese valor en el header `X-Request-ID` de la respuesta. (US-10)
- AC-47: IF el request trae un header `X-Request-ID` válido THEN the system SHALL reutilizar ese valor como `correlation_id`. (US-10)
- AC-48: IF el backend responde un error por `HTTPException`, `RequestValidationError` o una subclase de `DomainError` THEN the system SHALL responder con `Content-Type: application/problem+json` y un cuerpo RFC 9457 con `type`, `title`, `status`, `detail`, `instance` y `correlation_id`, declarado en `responses=` de cada ruta para que Orval genere su tipo. (US-10)
- AC-49: WHEN el mutator del frontend recibe una respuesta `application/problem+json` THEN the system SHALL lanzar un `ApiError` que exponga `status`, `title`, `detail` y `correlationId`. (US-10)
- AC-50: IF un log del backend incluye un valor `SecretStr` o una clave cuyo nombre contiene `password`, `token`, `secret` o `api_key` THEN the system SHALL reemplazar el valor por `"***"` antes de emitirlo. (US-9, US-10)
- AC-51: WHEN se inspecciona `app/domain/` THEN the system SHALL definir los tipos `Price`, `Quantity` y `Money` como `Annotated[Decimal, ...]`, serializados como string en JSON, y un contexto decimal con redondeo explícito `ROUND_HALF_EVEN`. (US-11)
- AC-52: IF un esquema de `app/schemas/` o un modelo ORM declara un campo de precio, cantidad o monto con tipo `float`, o una columna monetaria con un tipo distinto de `Numeric(p, s)`, THEN the system SHALL hacer fallar `uv run pytest` con un test de arquitectura que nombre el campo. (US-11)
- AC-53: WHEN se ejecuta `uv run pytest` THEN the system SHALL verificar con Hypothesis que el redondeo a tick y las operaciones de `Money` cumplen idempotencia del redondeo, conmutatividad de la suma y ausencia de pérdida de precisión, con al menos 200 ejemplos por propiedad. (US-7, US-11)
- AC-54: WHEN se inspecciona `app/core/` THEN the system SHALL contener un protocolo `Clock` con `now() -> datetime` que devuelve fechas en UTC con zona horaria, provisto como dependencia de FastAPI e inyectable en tests. (US-11)
- AC-55: WHEN se inspecciona `backend/CLAUDE.md` THEN the system SHALL documentar como reglas obligatorias para la primera feature que envíe órdenes: `client_order_id` único con constraint `UNIQUE`, controles de riesgo previos al envío (máximo por orden, por notional y por posición, y órdenes por segundo), un kill switch persistido que bloquee todo envío, una tabla de auditoría de órdenes de solo inserción y rate limiting hacia Matriz. (US-11, US-12)
- AC-56: WHEN se inspecciona `frontend/CLAUDE.md` THEN the system SHALL documentar que todo envío de órdenes requiere confirmación con `modal.confirm` de `App.useApp()` mostrando lado, cantidad, precio y notional; que el botón de envío queda `loading` y `disabled` mientras la mutación está pendiente; que precios y cantidades viajan como string; y que los números se formatean con los formatters de `src/utils/format.ts`. (US-11, US-12)
- AC-57: WHEN se inspecciona `frontend/src/utils/format.ts` THEN the system SHALL exportar formatters de precio y cantidad basados en `Intl.NumberFormat` con locale `es-AR`, con instancias reutilizadas y tests unitarios. (US-11)
- AC-58: WHEN se inspeccionan `.octo/steering/product.md`, `.octo/steering/tech.md` y `.octo/steering/structure.md` THEN the system SHALL describir en cada uno, sin secciones vacías ni placeholders, el propósito del producto (trading manual asistido y algorítmico sobre Matriz), el stack con sus comandos de gate y la estructura con las reglas de capas de backend y frontend. (US-12)
- AC-59: WHEN se inspecciona `CLAUDE.md` en la raíz THEN the system SHALL contener como máximo 200 líneas, con contexto, comandos, Definición de terminado y checklist, y SHALL remitir a `backend/CLAUDE.md` y `frontend/CLAUDE.md` para las convenciones de cada módulo. (US-12)
- AC-60: WHEN una regla de `CLAUDE.md` (raíz o de un módulo) queda verificada por una herramienta THEN the system SHALL documentarla en una línea que nombre la herramienta o el comando que la hace cumplir. (US-12)
- AC-61: WHEN se abre un PR THEN the system SHALL precargar la descripción desde `.github/pull_request_template.md` con: link al spec de Octo, checklist de §10 de `CLAUDE.md`, confirmación de que se commitearon juntos `openapi.json` y `generated/` si cambió el contrato, capturas si cambió la UI y una sección de riesgo y rollback. (US-12)
- AC-62: WHEN se ejecutan todos los gates de este spec sobre el esqueleto actual THEN the system SHALL terminar cada uno con código 0, sin reglas desactivadas fuera de las listadas con justificación según AC-23. (US-1, US-2, US-3, US-5, US-6, US-7)

## Out of Scope

- Productos SaaS o de pago (SonarCloud, Codecov, Snyk, CodeRabbit, Chromatic). La decisión es solo OSS o gratuito.
- `anthropics/claude-code-action` como check requerido: consume tokens de API. La revisión con IA sigue siendo local, con el agente `code-reviewer`.
- Mutation testing (mutmut) como gate: puede correr a mano o de noche más adelante.
- Lighthouse CI y presupuestos de performance en runtime.
- Implementar envío de órdenes, controles de riesgo, kill switch, auditoría o rate limiting: este spec fija las reglas y los tipos base; cada mecanismo llega con la primera feature de órdenes.
- Reemplazar mypy por pyrefly o ty: ty sigue en `0.0.x`; pyrefly se puede evaluar más adelante como chequeo no bloqueante.
- Despliegue continuo (CD), entornos de staging y observabilidad en producción (OpenTelemetry exportando a un backend).
- Reescribir el historial de commits existente para cumplir Conventional Commits.

## Non-Functional Requirements

- **Una sola fuente de verdad:** cada gate se define una vez, en un script por módulo, y lo invocan CI, `lefthook`, el hook `Stop` de Claude Code, el hook de Octo y la ejecución manual. Ningún archivo de configuración duplica la lista de comandos.
- **Velocidad local:**
  - El hook `pre-commit` termina en menos de 20 s para un cambio de hasta 10 archivos en un módulo, con dependencias ya instaladas.
  - El hook `PostToolUse` termina en menos de 10 s por archivo.
- **Velocidad de CI:** un PR que toca un solo módulo completa `ci-ok` en menos de 10 min con caché caliente.
- **Bloqueante desde el día 1:** ningún gate de este spec queda en modo advertencia. Toda excepción figura en la configuración con un comentario que la justifica.
- **Solo OSS o gratis:** todas las herramientas nuevas tienen licencia OSI o son gratuitas para repos privados en GitHub Actions.
- **Dependencias nuevas justificadas (regla de §2 de `CLAUDE.md`):** ninguna duplica una responsabilidad de la tabla del stack. El plan las justifica una por una.
  - Backend: `import-linter`, `pytest-cov`, `pytest-randomly`, `hypothesis`, `schemathesis`, `testcontainers`, `alembic`, `structlog`, `asgi-correlation-id`.
  - Frontend: `dependency-cruiser`, `knip`, `@vitest/coverage-v8`, `@axe-core/playwright`, `size-limit`.
  - Repo: `lefthook`, `gitleaks`, `actionlint`, `zizmor`, `squawk`, `osv-scanner` y Renovate (como app de GitHub).
- **Sin secretos versionados:** los tokens viven solo como secrets de GitHub Actions o en el `.env` local, ignorado por git.
- **Documentación coherente:** `README.md`, `CLAUDE.md` (raíz y módulos) y `.octo/steering/` describen los mismos comandos que ejecutan los scripts de gate.

## Open Questions

- [x] ¿Qué umbrales iniciales de cobertura usamos? — **Resolved:** Opción A: backend 85 % de branches y frontend 70 % de líneas y branches, subiendo de a 5 puntos por trimestre.
  - Opción B: 80 % en ambos desde el inicio.
- [x] ¿Cómo se mockea la red en los tests unitarios del frontend? — **Resolved:** Opción A: adoptar MSW 2 con `onUnhandledRequest: "error"` y handlers generados por Orval (`mock: true`). Se actualiza §8 de `CLAUDE.md` y se suman `msw` y `@faker-js/faker`.
  - Opción B: mantener `vi.stubGlobal("fetch")`.
- [x] ¿Cómo se divide `CLAUDE.md`? — **Resolved:** Opción A: `CLAUDE.md` raíz más `backend/CLAUDE.md` y `frontend/CLAUDE.md`.
  - Opción B: `.claude/rules/*.md` con frontmatter `paths:`.
- [x] ¿Qué herramienta gestiona los hooks de git? — **Resolved:** Opción A: `lefthook`, binario único y políglota, con `root:` por módulo.
  - Opción B: `vp staged` de Vite+.

Riesgos técnicos a resolver en un spike al inicio de Build (no bloquean estos requisitos):
- Si los `overrides` de Oxlint combinan o reemplazan las opciones de `no-restricted-imports`, si `import/no-cycle` resuelve el alias `@/` y los nombres exactos de las reglas en la versión de Oxlint que trae `vp`.
- Si `uv audit` sigue en preview. En ese caso, AC-43 usa `pip-audit` sobre `uv export --frozen`.
- Si `exactOptionalPropertyTypes` es compatible con el código que genera Orval 8 y con los tipos de Ant Design 6.
- Cómo seguir con Renovate los tags git de `market-libs` declarados en `[tool.uv.sources]`.

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Qué umbrales iniciales de cobertura usamos?** — Backend 85 % de branches (`fail_under = 85`) y frontend 70 % de líneas y branches, subiendo de a 5 puntos por trimestre.
- **¿Cómo se mockea la red en los tests unitarios del frontend?** — MSW 2 con `onUnhandledRequest: "error"` y handlers generados por Orval (`mock: true`). Sigue siendo un mock en el borde que ejercita el mutator real. Se actualiza §8 de `CLAUDE.md`. Los e2e siguen usando `page.route`.
- **¿Cómo se divide `CLAUDE.md`?** — `CLAUDE.md` raíz (contexto, comandos, Definición de terminado, checklist) más `backend/CLAUDE.md` y `frontend/CLAUDE.md` con las convenciones de cada módulo.
- **¿Qué herramienta gestiona los hooks de git?** — `lefthook`, con un único `lefthook.yml` en la raíz que invoca `scripts/gate.sh <módulo> quick`.
