# Tasks — Guardas de calidad y buenas prácticas

### Wave 1
- [x] T1: Spike de verificación, sin cambios en el repo: overrides de Oxlint y `import/no-cycle` con `@/`, nombres de reglas y soporte de `no-restricted-properties` en el Oxlint de `vp` 1.7, existencia de `vp check --fix`, `exactOptionalPropertyTypes` contra `generated/` y AntD, estado de `uv audit`, versión de `squawk-cli` vía `uvx`, firma del transporte ASGI de Schemathesis 4 y extracción de fuentes git de `[tool.uv.sources]` por Renovate — _outcome: cada incógnita de Risks tiene una entrada con la decisión tomada en Critical Decisions_
- [x] T2 @backend-expert: Actualizar `backend/pyproject.toml` (dependencias, Ruff ampliado con `flake8-type-checking`, pytest, coverage e import-linter), regenerar `backend/uv.lock`, crear `app/services/__init__.py`, `app/domain/__init__.py` y `app/api/deps.py` con `SessionDep`, corregir las violaciones nuevas y extender `tests/test_tooling.py` — _outcome: `ruff check`, `ruff format --check`, `mypy .`, `lint-imports` y `pytest` (cobertura ≥ 85 %) salen con 0 desde `backend/` (AC-20, AC-22, AC-23, AC-25, AC-33)_
- [x] T3 @frontend-expert: Agregar a `frontend/package.json` las devDependencies nuevas, los scripts `lint:arch`, `lint:unused` y `size` y el bloque `size-limit`, regenerar `frontend/pnpm-lock.yaml`, crear `frontend/.dependency-cruiser.cjs` y `frontend/knip.config.ts` — _outcome: `vp install`, `vp run lint:arch` y `vp run lint:unused` salen con 0 sobre el esqueleto (AC-29, AC-31)_

### Wave 2 (depends on T1, T2, T3)
- [x] T4 @backend-expert: Crear `app/domain/numeric.py` y `app/core/clock.py`, agregar `ClockDep` a `app/api/deps.py` y escribir `tests/test_numeric.py`, `tests/test_clock.py` y `tests/test_domain_types.py` — _outcome: `uv run pytest` pasa con las tres propiedades de Hypothesis a 200 ejemplos y con el modelo y la tabla probe detectados (AC-51, AC-52, AC-53, AC-54)_
- [x] T5 @backend-expert: Implementar errores RFC 9457 (`app/schemas/problem.py`, `app/domain/errors.py`, `app/api/errors.py`, `PROBLEM_RESPONSES` en `app/api/router.py:7` y `register_exception_handlers` en `app/main.py:40`), regenerar `backend/openapi.json` y agregar `tests/test_errors.py` — _outcome: `uv run pytest` en verde con 404, 422, `DomainError` y 500 en `application/problem+json`, y `openapi.json` declara `ProblemDetails` (AC-48)_
- [x] T6 @database-expert: Inicializar Alembic async (`backend/alembic.ini`, `backend/migrations/**`) con `Base.metadata` y la URL resuelta desde la opción o `Settings`, y crear `tests/test_migrations.py` marcado `db` con testcontainers — _outcome: con Docker, `uv run pytest -m db --no-cov` corre `upgrade head` y `alembic check` en verde (AC-35, AC-40, AC-41)_
- [x] T7 @frontend-expert: Ampliar los bloques `lint` y `test.coverage` de `frontend/vite.config.ts`, agregar los tres flags a `frontend/tsconfig.json` y `frontend/tsconfig.node.json` y corregir las violaciones en `src/` — _outcome: `vp check` sin errores ni warnings y `vp test run --coverage` sobre el 70 % salen con 0 (AC-26, AC-27, AC-28, AC-32, AC-36)_

### Wave 3 (depends on T4, T5, T6, T7)
- [x] T8 @backend-expert: Implementar observabilidad: `app/core/logging.py`, `app/api/middleware.py`, `CorrelationIdMiddleware` y `configure_logging` en `app/main.py`, `log_config=None` en `app/__main__.py:17`, y `tests/test_logging.py` — _outcome: `uv run pytest` en verde con `X-Request-ID` generado y reutilizado, `correlation_id` en el JSON y secretos como `***` (AC-46, AC-47, AC-50)_
- [x] T9 @backend-expert: Crear `backend/tests/test_contract.py` con Schemathesis contra la app ASGI y el `openapi.json` versionado — _outcome: `uv run pytest` en verde y un desvío de contrato provocado a mano hace fallar el test (AC-34)_
- [x] T10 @frontend-expert: Activar `mock: true` en `frontend/orval.config.ts`, regenerar `src/api/generated/`, crear `src/test/server.ts`, registrar el ciclo de MSW en `src/test/setup.ts` y migrar `HomeScreen.test.tsx` de `vi.stubGlobal` a handlers de MSW — _outcome: `vp test run --coverage` en verde y `grep -rn stubGlobal frontend/src` no encuentra nada (Resolved Decisions)_
- [x] T11 @frontend-expert: Crear `src/utils/format.ts` y `src/utils/format.test.ts` — _outcome: `vp test run` pasa con `formatPrice("1234.5", 2) === "1.234,50"`, un string de 18 dígitos sin pérdida e instancias cacheadas (AC-57)_
- [x] T12 @frontend-expert: Crear `frontend/e2e/a11y.spec.ts` con axe sobre Home y 404, corrigiendo las violaciones que aparezcan en `src/screens/*/*.tsx` o `src/layouts/` — _outcome: `vp run e2e` sale con 0 y sin violaciones WCAG 2.2 AA (AC-37, AC-38)_

### Wave 4 (depends on T10)
- [x] T13 @frontend-expert: Extender `ApiError` en `src/api/mutator.ts` con `title`, `detail` y `correlationId` desde `ProblemDetails`, y crear `src/api/mutator.test.ts` con handlers MSW — _outcome: `vp test run` pasa con un 500 `problem+json` convertido en `ApiError` con los tres campos y un 502 no-JSON con los tres en `undefined` (AC-49)_

### Wave 5 (depends on T8, T9, T11, T12, T13)
- [x] T14: Crear `scripts/gate.sh`, `scripts/verify-guards.sh` y `scripts/guard-probes/**`, medir el bundle para fijar el límite de `size-limit` en `frontend/package.json` y agregar `**/_probe*`, `coverage/`, `.coverage`, `htmlcov/` y `.hypothesis/` a `.gitignore` — _outcome: `scripts/gate.sh backend full` y `scripts/gate.sh frontend full` salen con 0, lo que incluye que cada probe hace fallar su herramienta con el id esperado (AC-19, AC-21, AC-22, AC-24, AC-27, AC-28, AC-30, AC-39)_

### Wave 6 (depends on T14)
- [x] T15: Crear `lefthook.yml` y `scripts/hooks/{check-generated-sync,gitleaks-staged,commit-msg}.sh` — _outcome: los escenarios de AC-8 a AC-13 de Verification se comportan como se espera (AC-8, AC-9, AC-10, AC-11, AC-12, AC-13)_
- [x] T16: Crear `.claude/settings.json` y `.claude/hooks/{guard-paths,fmt-lint-file,stop-gate}.sh`, y actualizar `instructions` en `.octo/hooks/code-validate-improve.json:10` — _outcome: los escenarios de AC-14 a AC-18 de Verification se cumplen en una sesión de Claude Code (AC-14, AC-15, AC-16, AC-17, AC-18)_
- [x] T17: Crear `.github/workflows/ci.yml` con los jobs `changes`, `backend`, `frontend`, `e2e`, `migrations`, `security`, `workflow-lint` y `ci-ok` — _outcome: actionlint y zizmor en verde localmente y el primer PR muestra todos los jobs con `ci-ok` en verde (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-38, AC-41, AC-42, AC-44)_
- [x] T18: Crear `scripts/audit.py` y `security-allowlist.toml` — _outcome: `python3 scripts/audit.py` sale con 0 y con 1 si se agrega una entrada vencida (AC-43)_
- [x] T19: Crear `renovate.json` — _outcome: `npx --yes --package renovate -- renovate-config-validator renovate.json` sale con 0 (AC-45)_
- [x] T20: Crear `.github/pull_request_template.md` y `.github/rulesets/main.json` — _outcome: un PR nuevo contra `main` se abre con la plantilla y, una vez aplicado el ruleset con `gh api`, exige `ci-ok` (AC-7, AC-61)_

### Wave 7 (depends on T15, T16, T17, T18, T19, T20)
- [x] T21 @docs-expert: Dividir `CLAUDE.md` en la raíz, `backend/CLAUDE.md` y `frontend/CLAUDE.md`, completar `.octo/steering/{product,tech,structure}.md` y actualizar la sección «Calidad y tests» de `README.md:145` (lefthook, gitleaks, `scripts/gate.sh`, `MARKET_LIBS_TOKEN`, ruleset y Renovate) — _outcome: los chequeos de AC-55 a AC-60 de Verification pasan (AC-7, AC-55, AC-56, AC-58, AC-59, AC-60)_

### Wave 8 (depends on T21)
- [x] T22: En un clon limpio, seguir el README, instalar lefthook, ejecutar `scripts/gate.sh` con `backend`, `frontend`, `e2e` y `migrations` en modo full, y recorrer la tabla Verification midiendo `pre-commit`, `PostToolUse` y CI — _outcome: todos los gates salen con 0, los tiempos cumplen los NFR y cualquier desvío queda registrado en Critical Decisions (AC-62)_
