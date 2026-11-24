# Plan: Guardas de calidad y buenas prácticas (backend, frontend y agentes)

> Convertir las convenciones de `CLAUDE.md` y las prácticas de FastAPI, React y del dominio trading en gates bloqueantes que corren con un mismo script (`scripts/gate.sh`) en cuatro lugares: cuando el agente edita o termina un turno, en el commit, en el hook de Octo y en CI. Appetite: L. Risk: medium.

## Approach

```mermaid
flowchart LR
  A["Spike: Oxlint, uv audit, TS flags, Renovate"] --> B["Config de herramientas por módulo"]
  B --> C["Código base: dominio, Clock, errores RFC 9457, logging, Alembic"]
  C --> D["scripts/gate.sh + verify-guards.sh"]
  D --> E["Consumidores: lefthook, hooks Claude/Octo, CI"]
  E --> F["Docs: CLAUDE.md por módulo, steering, README"]
  F --> G["Verificación en clon limpio"]
```

Vamos de adentro hacia afuera. Primero se configura cada herramienta dentro de su módulo, en `backend/pyproject.toml`, `frontend/vite.config.ts` y `frontend/package.json`, y se dejan en verde sobre el esqueleto. Después se escribe el código base que esas reglas exigen: tipos `Decimal`, `Clock`, errores RFC 9457, logging estructurado y Alembic. Recién entonces se arma el **único** punto de entrada, `scripts/gate.sh <módulo> <quick|full>`. Lefthook, los hooks de Claude Code, el hook de Octo y GitHub Actions solo invocan ese script, así que ninguno repite comandos (AC-19).

Alternativas descartadas:
- Definir los comandos en cada consumidor (YAML de CI, `lefthook.yml`, hooks): se desincronizan, que es justamente el problema de hoy.
- Lefthook para el gate completo: un `pre-commit` de varios minutos lleva a usar `--no-verify`. Por eso `quick` va en local y `full` en Stop, Octo y CI.
- Expresar las reglas de carpetas solo con Oxlint: compara el texto del import, no la ruta resuelta, y no puede expresar «una pantalla no importa otra». Esa regla va en dependency-cruiser.
- `claude-code-action` como revisión en el PR: consume tokens, fuera de alcance.

## Affected files

| File | Change |
|---|---|
| `scripts/gate.sh` | Nuevo. Único punto de entrada de los gates: `backend`, `frontend`, `e2e`, `migrations`, `changed`, `branch` y `file <ruta>`, en modo `quick` o `full` (AC-9, AC-10, AC-15, AC-16, AC-18, AC-19, AC-62) |
| `scripts/hooks/check-generated-sync.sh` | Nuevo. Guard de `generated/` sin `openapi.json`, invocado por lefthook (AC-11) |
| `scripts/hooks/commit-msg.sh` | Nuevo. Validación Conventional Commits, invocado por lefthook (AC-13) |
| `scripts/hooks/gitleaks-staged.sh` | Nuevo. Corre gitleaks sobre lo stageado; si el binario falta, falla con la instrucción de instalación (AC-12) |
| `scripts/verify-guards.sh` | Nuevo. Inyecta violaciones de prueba y exige que cada gate falle con la regla esperada (AC-21, AC-22, AC-24, AC-27, AC-28, AC-30) |
| `scripts/guard-probes/**` | Nuevo. Un archivo por violación: probes `.py` y `.tsx` que `verify-guards.sh` copia al módulo y luego borra (AC-24, AC-27, AC-28, AC-30) |
| `scripts/audit.py` | Nuevo. Corre pip-audit y OSV-Scanner, filtra por la allowlist y falla si hay hallazgos o entradas vencidas (AC-43) |
| `security-allowlist.toml` | Nuevo. Vulnerabilidades aceptadas, con `id`, `package`, `reason` y `expires` (AC-43) |
| `lefthook.yml` | Nuevo. `pre-commit` (gate `quick` por módulo, guard de `generated/`, gitleaks) y `commit-msg` (AC-8 a AC-13) |
| `renovate.json` | Nuevo (AC-45) |
| `.gitignore:23` | Agrega `coverage/`, `.coverage`, `htmlcov/`, `.hypothesis/` y `**/_probe*` |
| `.github/workflows/ci.yml` | Nuevo. Jobs `changes`, `backend`, `frontend`, `e2e`, `migrations`, `security`, `workflow-lint` y `ci-ok` (AC-1 a AC-6, AC-38, AC-41 a AC-44) |
| `.github/rulesets/main.json` | Nuevo. Ruleset de `main` para aplicar con `gh api` (AC-7) |
| `.github/pull_request_template.md` | Nuevo (AC-61) |
| `.claude/settings.json` | Nuevo. Hooks `PreToolUse`, `PostToolUse` y `Stop` (AC-14 a AC-17) |
| `.claude/hooks/guard-paths.sh` | Nuevo (AC-14) |
| `.claude/hooks/fmt-lint-file.sh` | Nuevo (AC-15) |
| `.claude/hooks/stop-gate.sh` | Nuevo (AC-16, AC-17) |
| `.octo/hooks/code-validate-improve.json:10` | `instructions` pasa a usar `scripts/gate.sh branch full` y deja de mencionar `npm run typecheck` (AC-18) |
| `.octo/steering/product.md` | Completo (AC-58) |
| `.octo/steering/tech.md` | Completo (AC-58) |
| `.octo/steering/structure.md` | Completo (AC-58) |
| `CLAUDE.md` | Se reduce a 200 líneas o menos y remite a los CLAUDE.md de cada módulo (AC-59, AC-60) |
| `backend/CLAUDE.md` | Nuevo. Convenciones del backend y reglas obligatorias para órdenes (AC-55, AC-60) |
| `frontend/CLAUDE.md` | Nuevo. Convenciones del frontend, reglas de UI de órdenes y MSW (AC-56, AC-60) |
| `README.md:145` | Sección «Calidad y tests»: `scripts/gate.sh`, lefthook, secret de CI y ruleset (AC-7) |
| `backend/pyproject.toml:17` | Dependencias nuevas en `dev` y runtime (AC-33 a AC-35, AC-40, AC-46) |
| `backend/pyproject.toml:32` | Ruff `extend-select`, `ignore` justificado, `banned-api` y `per-file-ignores` de tests (AC-23, AC-24) |
| `backend/pyproject.toml:46` | Pytest: `addopts` con cobertura, `filterwarnings = error` y marcador `db`; más `[tool.coverage.*]` y `[tool.importlinter]` (AC-20 a AC-22, AC-33) |
| `backend/uv.lock` | Regenerado |
| `backend/app/domain/__init__.py` | Nuevo |
| `backend/app/domain/numeric.py` | Nuevo. `Price`, `Quantity`, `Money`, `DECIMAL_CONTEXT` y `round_to_tick` (AC-51) |
| `backend/app/domain/errors.py` | Nuevo. `DomainError` (AC-48) |
| `backend/app/services/__init__.py` | Nuevo. Capa de servicios, vacía (AC-20) |
| `backend/app/core/clock.py` | Nuevo. `Clock`, `SystemClock` y `get_clock` (AC-54) |
| `backend/app/core/logging.py` | Nuevo. `configure_logging` y `redact_sensitive` (AC-46, AC-50) |
| `backend/app/api/deps.py` | Nuevo. `SessionDep` y `ClockDep` (AC-22, AC-54) |
| `backend/app/api/errors.py` | Nuevo. Handlers RFC 9457 y `PROBLEM_RESPONSES` (AC-48) |
| `backend/app/api/middleware.py` | Nuevo. Log de acceso estructurado por request (AC-46) |
| `backend/app/api/router.py:7` | `APIRouter(prefix="/api", responses=PROBLEM_RESPONSES)` (AC-48) |
| `backend/app/schemas/problem.py` | Nuevo. `ProblemDetails` y `ValidationIssue` (AC-48) |
| `backend/app/main.py:40` | `register_exception_handlers(app)` (T5); `CorrelationIdMiddleware`, `AccessLogMiddleware` y `configure_logging` en el `lifespan:21` (T8) (AC-46 a AC-48) |
| `backend/app/__main__.py:17` | `configure_logging` antes de uvicorn, `log_config=None` y `access_log=False` (AC-46) |
| `backend/app/db/session.py:24` | Sin cambios: `get_session` es la única puerta de `app.api` a la DB, vía `app/api/deps.py` (AC-22) |
| `backend/openapi.json` | Regenerado con `ProblemDetails` (AC-48) |
| `backend/alembic.ini` | Nuevo (AC-40) |
| `backend/migrations/env.py` | Nuevo. Plantilla async, `Base.metadata` y URL desde `Settings` (AC-40) |
| `backend/migrations/script.py.mako` | Nuevo (AC-40) |
| `backend/migrations/versions/.gitkeep` | Nuevo (AC-40) |
| `backend/tests/test_tooling.py:26` | Mantiene el chequeo de ANN y agrega: grupos de Ruff de AC-23, contratos de import-linter de AC-20 a AC-22 y `fail_under = 85` (AC-25) |
| `backend/tests/test_numeric.py` | Nuevo. Propiedades con Hypothesis (AC-53) |
| `backend/tests/test_domain_types.py` | Nuevo. Test de arquitectura contra `float` y `Numeric` (AC-52) |
| `backend/tests/test_clock.py` | Nuevo (AC-54) |
| `backend/tests/test_logging.py` | Nuevo (AC-46, AC-47, AC-50) |
| `backend/tests/test_errors.py` | Nuevo (AC-48) |
| `backend/tests/test_contract.py` | Nuevo. Schemathesis contra la app ASGI (AC-34) |
| `backend/tests/test_migrations.py` | Nuevo, marcado `db`. testcontainers, `upgrade head` y `alembic check` (AC-35, AC-41) |
| `frontend/package.json:6` | Dependencias nuevas, scripts `lint:arch`, `lint:unused` y `size`, más el bloque `size-limit` (AC-29, AC-31, AC-39) |
| `frontend/knip.config.ts` | Nuevo. Config de knip en TS para poder justificar cada `ignore*` con un comentario (AC-31) |
| `frontend/pnpm-lock.yaml` | Regenerado |
| `frontend/.dependency-cruiser.cjs` | Nuevo (AC-29, AC-30) |
| `frontend/vite.config.ts:30` | Bloque `lint` ampliado con overrides; `react/only-export-components` pasa de `warn` a `error` (AC-26 a AC-28) |
| `frontend/vite.config.ts:44` | Bloque `test` con `coverage` y umbrales (AC-36) |
| `frontend/tsconfig.json:21` | Agrega `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature` y `noImplicitReturns` (AC-32) |
| `frontend/tsconfig.node.json:17` | Los mismos tres flags, para que AC-32 valga en `tsconfig*.json` (AC-32) |
| `frontend/playwright.config.ts:9` | Sin cambios: ya tiene `forbidOnly`, `retries: 2` y `trace: "on-first-retry"` con `CI` (AC-38) |
| `frontend/orval.config.ts:8` | `output.mock: true` para generar handlers MSW (Resolved Decisions) |
| `frontend/src/api/generated/**` | Regenerado (con `*.msw.ts` y `ProblemDetails`); no se edita a mano |
| `frontend/src/api/mutator.ts:3` | `ApiError` expone `title`, `detail` y `correlationId` a partir de `ProblemDetails` (AC-49) |
| `frontend/src/api/mutator.test.ts` | Nuevo (AC-49) |
| `frontend/src/test/server.ts` | Nuevo. `setupServer()` de MSW |
| `frontend/src/test/setup.ts:7` | Ciclo de vida de MSW con `onUnhandledRequest: "error"`, importando de `vite-plus/test` |
| `frontend/src/screens/HomeScreen/HomeScreen.test.tsx` | Migra de `vi.stubGlobal` a MSW |
| `frontend/src/utils/format.ts` | Nuevo (AC-57) |
| `frontend/src/utils/format.test.ts` | Nuevo (AC-57) |
| `frontend/e2e/a11y.spec.ts` | Nuevo (AC-37) |

## Repo: scripts de gate

**`scripts/gate.sh`** es la única definición de cada gate (AC-19):

```bash
#!/usr/bin/env bash
# Uso: scripts/gate.sh <backend|frontend|e2e|migrations|changed|branch> [quick|full]   (default: full)
#      scripts/gate.sh file <ruta-relativa-a-la-raíz>                                     (hook PostToolUse)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
target="${1:?Uso: scripts/gate.sh <módulo> [quick|full]}"; mode="${2:-full}"

backend_quick() { cd "$ROOT/backend" && uv run ruff format . && uv run ruff check --fix . && uv run mypy . && uv run lint-imports; }
backend_full()  { cd "$ROOT/backend" && uv run ruff check . && uv run ruff format --check . && uv run mypy . \
                  && uv run lint-imports && uv run pytest && "$ROOT/scripts/verify-guards.sh" backend; }
frontend_quick() { cd "$ROOT/frontend" && vp check --fix && vp run lint:arch; }
frontend_full()  { cd "$ROOT/frontend" && vp check && vp run lint:arch && vp run lint:unused \
                   && vp test run --coverage && vp build && vp run size && "$ROOT/scripts/verify-guards.sh" frontend; }
e2e_full()       { cd "$ROOT/frontend" && vp run e2e; }
# PostgreSQL 17 lo levanta testcontainers (requiere Docker). `upgrade --sql` es offline: no conecta a ninguna DB,
# pero env.py necesita una DATABASE_URL sintácticamente válida (en CI se exporta una ficticia).
migrations_full() { cd "$ROOT/backend" && uv run pytest -m db --no-cov \
                    && uv run alembic upgrade head --sql | uvx squawk-cli@<versión fijada en T1> --assume-in-transaction; }
file_check() {  # formatea y lintea UN archivo; lo usa .claude/hooks/fmt-lint-file.sh (AC-15)
  local f="$1"
  case "$f" in
    backend/*.py)  cd "$ROOT/backend"  && uv run ruff format "${f#backend/}" && uv run ruff check --fix "${f#backend/}" ;;
    frontend/src/api/generated/*) return 0 ;;
    frontend/*.ts|frontend/*.tsx) cd "$ROOT/frontend" && vp fmt "${f#frontend/}" && vp lint "${f#frontend/}" ;;
    *) return 0 ;;
  esac
}
run_modules() {  # $1 = lista de archivos cambiados; corre el gate de cada módulo tocado y acumula fallas
  local rc=0
  grep -q '^backend/'  <<<"$1" && { "$0" backend  "$mode" || rc=1; }
  grep -q '^frontend/' <<<"$1" && { "$0" frontend "$mode" || rc=1; }
  return "$rc"
}
untracked() { git -C "$ROOT" ls-files --others --exclude-standard; }
changed() {  # cambios sin commitear (tracked + untracked) respecto de HEAD — hook Stop (AC-16)
  run_modules "$( { git -C "$ROOT" diff --name-only HEAD; untracked; } | sort -u)"
}
branch() {   # todo lo que la rama cambió respecto de origin/main, commiteado o no — hook de Octo (AC-18)
  local base; base="$(git -C "$ROOT" merge-base HEAD origin/main 2>/dev/null || git -C "$ROOT" rev-parse HEAD)"
  run_modules "$( { git -C "$ROOT" diff --name-only "$base"; untracked; } | sort -u)"
}

case "$target:$mode" in
  backend:quick)  backend_quick ;;   backend:full)  backend_full ;;
  frontend:quick) frontend_quick ;;  frontend:full) frontend_full ;;
  e2e:full)       e2e_full ;;        migrations:full) migrations_full ;;
  changed:*)      changed ;;         branch:*)      branch ;;
  file:*)         file_check "$mode" ;;   # acá $2 es la ruta, no el modo
  *) echo "Uso: scripts/gate.sh <backend|frontend> [quick|full] | <e2e|migrations> [full] | <changed|branch> [quick|full] | file <ruta>" >&2; exit 64 ;;
esac
```

Contrato de salida: `0` si todo pasa, `1` si falla algún comando (su salida queda en stdout/stderr sin filtrar), `64` si los argumentos son inválidos. `changed` y `branch` corren **todos** los módulos tocados aunque falle el primero, para que el agente vea todos los errores de una vez; si no hay cambios en ningún módulo, salen con `0`.

En el gate `full`, el frontend no corre e2e: lo hace el job `e2e` de CI. La §9 de `CLAUDE.md` lo exige solo si se tocó un flujo cubierto.

**`scripts/verify-guards.sh <backend|frontend>`**: por cada probe en `scripts/guard-probes/<módulo>/`, lo copia a una ruta temporal dentro del módulo (`backend/app/domain/_probe.py`, `frontend/src/screens/_ProbeA/...`), corre la herramienta correspondiente, exige exit distinto de 0 y que la salida contenga el id esperado, y borra el probe con `trap`:

| Probe | Herramienta | Debe contener |
|---|---|---|
| `backend/utcnow.py` | `ruff check` | `DTZ003` (AC-24) |
| `backend/naive_now.py` | `ruff check` | `DTZ005` (AC-24) |
| `backend/async_sleep.py` | `ruff check` | `ASYNC251` (AC-24) |
| `backend/requests_import.py` | `ruff check` | `TID251` (AC-24) |
| `backend/domain_imports_fastapi.py` (en `app/domain/`) | `lint-imports` | `Dominio puro` y `app.domain._probe -> fastapi` (AC-21) |
| `backend/api_imports_db.py` (en `app/api/routes/`) | `lint-imports` | `API sin acceso directo a la DB` y `-> app.db` (AC-22) |
| `frontend/raw-fetch.tsx` | `vp lint` | `no-restricted-globals` (AC-27) |
| `frontend/axios.tsx` | `vp lint` | `no-restricted-imports` (AC-27) |
| `frontend/enum.ts` | `vp check` | `erasableSyntaxOnly` / TS1294 (AC-28) |
| `frontend/deep-relative.tsx` | `vp lint` | `no-restricted-imports` (AC-28) |
| `frontend/screen-to-screen/` | `vp run lint:arch` | `screen-no-otra-screen` (AC-30) |
| `frontend/component-to-api/` | `vp run lint:arch` | `components-limites` (AC-30) |
| `frontend/cycle/` | `vp run lint:arch` | `no-circular` (AC-30) |
| `frontend/hook-to-component/` | `vp run lint:arch` | `hooks-limites` (AC-30) |
| `frontend/utils-to-api/` | `vp run lint:arch` | `utils-constants-puros` (AC-30) |
| `frontend/layout-to-screen-internal/` | `vp run lint:arch` | `screen-via-index` (AC-30) |

AC-30 exige además los dos archivos involucrados: `verify-guards.sh` comprueba que la salida de depcruise contenga la ruta del probe origen y la del destino (`--output-type err` las imprime como `origen → destino`).

## CI (GitHub Actions)

`.github/workflows/ci.yml` (todas las acciones fijadas por SHA con un comentario `# vX.Y.Z`):

```yaml
name: ci
on:
  pull_request: { branches: [main] }
  push: { branches: [main] }
permissions: {}                                   # AC-3
concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }

jobs:
  changes:
    runs-on: ubuntu-latest
    permissions: { contents: read, pull-requests: read }
    outputs: { backend: ${{ steps.f.outputs.backend }}, frontend: ${{ steps.f.outputs.frontend }} }
    steps:
      - uses: actions/checkout@<sha> { with: { persist-credentials: false } }
      - id: f
        uses: dorny/paths-filter@<sha>            # AC-2
        with:
          filters: |
            backend:  ['backend/**', 'scripts/**', '.github/workflows/**']
            frontend: ['frontend/**', 'backend/openapi.json', 'scripts/**', '.github/workflows/**']

  backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@<sha> { with: { persist-credentials: false } }
      - name: Acceso a market-libs                # AC-4, AC-5
        env: { MARKET_LIBS_TOKEN: "${{ secrets.MARKET_LIBS_TOKEN }}" }
        run: |
          if [ -z "${MARKET_LIBS_TOKEN}" ]; then
            echo "::error::Falta el secret MARKET_LIBS_TOKEN (GitHub App o PAT con lectura de gravity-quant/market-libs)"; exit 1
          fi
          git config --global url."https://x-access-token:${MARKET_LIBS_TOKEN}@github.com/".insteadOf "ssh://git@github.com/"
      - uses: astral-sh/setup-uv@<sha> { with: { enable-cache: true, cache-dependency-glob: backend/uv.lock } }   # AC-6
      - run: uv sync --frozen
        working-directory: backend
      - run: scripts/gate.sh backend full

  frontend:            # if: needs.changes.outputs.frontend == 'true'; permissions: { contents: read }
    # pnpm/action-setup + actions/setup-node (cache: pnpm, cache-dependency-path: frontend/pnpm-lock.yaml)   AC-6
    # pnpm install --frozen-lockfile (en frontend/); echo "$PWD/frontend/node_modules/.bin" >> "$GITHUB_PATH"
    #   → `vp` es el bin del devDependency local `vite-plus` (frontend/package.json:31); no se usa el instalador global
    # scripts/gate.sh frontend full
  e2e:                 # if: needs.changes.outputs.frontend == 'true'; mismo setup que frontend
    # pnpm exec playwright install --with-deps chromium; scripts/gate.sh e2e full
    # if: failure() → actions/upload-artifact con frontend/test-results/ (traces), retention-days: 7   AC-38
  migrations:          # if: needs.changes.outputs.backend == 'true'; mismo paso de market-libs y setup-uv que backend
    # env: DATABASE_URL=postgresql+psycopg://ci:ci@localhost:5432/ci  (ficticia: solo la usa `upgrade --sql` offline)
    # scripts/gate.sh migrations full  → testcontainers levanta postgres:17 con el Docker del runner   AC-35, AC-41, AC-42
  security:            # siempre; permissions: { contents: read }; checkout con fetch-depth: 0 (gitleaks necesita historial)
    # gitleaks (binario de release fijado + sha256) `gitleaks git --redact --log-opts="$BASE..HEAD"`
    #   BASE = github.event.pull_request.base.sha en PR, github.event.before en push
    # setup-uv; python3 scripts/audit.py                                                AC-43
  workflow-lint:       # siempre; permissions: { contents: read }
    # actionlint (binario de release fijado + sha256) + `uvx zizmor@<versión> --min-severity low .github/workflows`   AC-44

  ci-ok:                                          # AC-1, AC-2: único check requerido
    if: always()
    needs: [changes, backend, frontend, e2e, migrations, security, workflow-lint]
    runs-on: ubuntu-latest
    permissions: {}
    steps:
      - env: { RESULTS: "${{ join(needs.*.result, ' ') }}" }
        run: |
          for r in $RESULTS; do case "$r" in success|skipped) ;; *) echo "::error::job en estado $r"; exit 1;; esac; done
```

Contratos:
- **Filtros:** un job omitido por el filtro termina como `skipped` y `ci-ok` lo acepta.
- **Workflows sin filtro:** `security` y `workflow-lint` corren siempre.
- **Token de `market-libs`:** el secret es `MARKET_LIBS_TOKEN`, un PAT fine-grained con `contents: read` solo sobre `gravity-quant/market-libs` y vencimiento de 90 días (default elegido: es el camino más corto y el que nombra AC-5). La alternativa GitHub App (`actions/create-github-app-token` con `MARKET_LIBS_APP_ID` y `MARKET_LIBS_APP_KEY`) queda documentada en el README como mejora; ver Open Questions.
- **`security-allowlist.toml`** (AC-43), contrato que lee `scripts/audit.py`:

```toml
# Cada entrada se revisa antes de `expires`; una entrada vencida hace fallar el job.
[[ignore]]
id = "GHSA-xxxx-xxxx-xxxx"        # o CVE / PYSEC / OSV id
ecosystem = "PyPI"                # "PyPI" | "npm"
package = "nombre"
reason = "No alcanzable: solo se usa en tests"
expires = 2027-02-28              # fecha TOML; máximo 90 días desde que se agrega
```

- **`scripts/audit.py`** (stdlib + `tomllib`, sin dependencias): corre
  `uv export --frozen --no-hashes --no-emit-package market-data-client --no-emit-package matriz-client` (las fuentes git privadas no están en PyPI ni en OSV) → `uvx pip-audit@<versión> --strict --disable-pip --no-deps -r <archivo> -f json`, y `osv-scanner scan source --lockfile frontend/pnpm-lock.yaml --format json`. Imprime `ecosystem package version id fix_versions` por hallazgo no permitido y por cada entrada vencida, y sale con `1` si hay al menos uno; `0` en otro caso.
- **Ruleset de `main`**, en `.github/rulesets/main.json`:

```json
{ "name": "main", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [ { "type": "pull_request", "parameters": { "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": true,
               "require_code_owner_review": false, "require_last_push_approval": false, "required_review_thread_resolution": true } },
             { "type": "required_status_checks", "parameters": { "strict_required_status_checks_policy": true,
               "required_status_checks": [ { "context": "ci-ok" } ] } },
             { "type": "non_fast_forward" }, { "type": "deletion" } ] }
```

Se aplica con `gh api repos/{owner}/{repo}/rulesets -X POST --input .github/rulesets/main.json` (AC-7).

- **`.github/pull_request_template.md`** (AC-61):

```markdown
## Spec
Octo: `.octo/specs/<slug>/` (link) — o «sin spec» con el motivo.

## Qué cambia y por qué

## Checklist (§10 de CLAUDE.md)
- [ ] (copia literal de los ítems de la checklist del CLAUDE.md raíz)

## Contrato de la API
- [ ] No cambió el contrato
- [ ] Cambió: `backend/openapi.json` y `frontend/src/api/generated/` van en este mismo PR

## Capturas (si cambió la UI)

## Riesgo y rollback
- Riesgo:
- Cómo revertir:
```

**`renovate.json`** (AC-45):

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "helpers:pinGitHubActionDigests", ":semanticCommits"],
  "minimumReleaseAge": "7 days",
  "packageRules": [
    { "matchFileNames": ["backend/**"],  "groupName": "backend" },
    { "matchFileNames": ["frontend/**"], "groupName": "frontend" },
    { "matchManagers": ["github-actions"], "groupName": "github-actions" },
    { "matchDepNames": ["market-data-client", "matriz-client"], "groupName": "market-libs",
      "minimumReleaseAge": "0 days", "versioning": "regex:^(?<compatibility>.+)-v(?<major>\\d+)\\.(?<minor>\\d+)\\.(?<patch>\\d+)$" }
  ]
}
```

T1 confirma cómo extrae Renovate las fuentes git de `[tool.uv.sources]`. Si no las detecta, se agrega un `customManagers` de tipo regex sobre `backend/pyproject.toml`.

## Capa de agentes (Claude Code y Octo)

`.claude/settings.json` (versionado; `.claude/settings.local.json` sigue ignorado):

```json
{
  "hooks": {
    "PreToolUse":  [{ "matcher": "Edit|Write|MultiEdit|NotebookEdit",
                      "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard-paths.sh" }] }],
    "PostToolUse": [{ "matcher": "Edit|Write|MultiEdit",
                      "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/fmt-lint-file.sh", "timeout": 60 }] }],
    "Stop":        [{ "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/stop-gate.sh", "timeout": 900 }] }]
  }
}
```

Los tres scripts leen el JSON de stdin con `jq` (`/usr/bin/jq` en macOS; queda documentado como prerrequisito):

- **`guard-paths.sh`** (AC-14):
  - `path=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')`, normalizado relativo a `$CLAUDE_PROJECT_DIR`.
  - Patrones bloqueados: `frontend/src/api/generated/*`, `backend/openapi.json`, `.env`, `.env.*` (excepto `.env.example`), `backend/uv.lock` y `frontend/pnpm-lock.yaml`.
  - Si coincide, escribe en stderr `Archivo generado/protegido: <path>. Regeneralo con: <comando>` y sale con `exit 2`. El comando sugerido es `uv run python -m app.scripts.export_openapi`, `vp run generate:api`, `uv lock` o `vp install` según el archivo; para `.env`, que lo edite una persona.
- **`fmt-lint-file.sh`** (AC-15):
  - Extrae la ruta igual que `guard-paths.sh` y llama `scripts/gate.sh file "$rel"`. No repite comandos de ruff ni de `vp` (AC-19): la lista vive en `file_check` de `gate.sh`.
  - Cubre `*.py` bajo `backend/` y `*.ts`/`*.tsx` bajo `frontend/` (incluido `e2e/`), excepto `frontend/src/api/generated/`. Otros archivos: `exit 0`.
  - Si `gate.sh` sale distinto de 0, la salida va a stderr y el hook sale con `exit 2`.
- **`stop-gate.sh`** (AC-16, AC-17):
  - Si `jq -r '.stop_hook_active'` es `true`, sale con `exit 0`.
  - Si no, corre `scripts/gate.sh changed full` (solo módulos con cambios sin commitear; sin cambios sale con 0). Si falla, escribe en stderr las últimas 120 líneas y sale con `exit 2`.

`.octo/hooks/code-validate-improve.json:10` cambia la clave `instructions`, paso 1 (AC-18):
`"1. Run \`scripts/gate.sh branch full\` via Bash from the repo root and read the output. ..."`
Se usa `branch` y no `changed` porque Octo puede commitear al cerrar cada tarea: `changed` daría verde sin verificar nada. El resto de los pasos queda igual, salvo que «typecheck result» pasa a «gate result».

Limitación conocida: un agente puede escribir archivos protegidos usando `Bash` en lugar de `Edit`. La red de seguridad es el guard de `generated/` en lefthook (AC-11) más CI (`test_openapi_export.py` y el drift del cliente). Queda registrada en Risks.

## Hooks de git (lefthook)

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    backend:
      glob: "backend/**/*.py"
      run: scripts/gate.sh backend quick          # AC-9
      stage_fixed: true
    frontend:
      glob: "frontend/**/*.{ts,tsx}"
      run: scripts/gate.sh frontend quick         # AC-10
      stage_fixed: true
    generated-sync:                               # AC-11
      run: scripts/hooks/check-generated-sync.sh
    gitleaks:                                     # AC-12
      run: scripts/hooks/gitleaks-staged.sh
commit-msg:
  commands:
    conventional:                                 # AC-13
      run: scripts/hooks/commit-msg.sh {1}
```

La lógica vive en scripts bash y no en el YAML: lefthook ejecuta `run` con `sh`, y `<<<` o `${#var}` no existen en `dash`. Contratos:

```bash
# scripts/hooks/check-generated-sync.sh — exit 1 si generated/ está stageado sin openapi.json
staged="$(git diff --cached --name-only)"
if grep -q '^frontend/src/api/generated/' <<<"$staged" && ! grep -qx 'backend/openapi.json' <<<"$staged"; then
  echo "frontend/src/api/generated/ cambió sin backend/openapi.json." >&2
  echo "Flujo (frontend/CLAUDE.md, «Flujo para cambiar el contrato»): uv run python -m app.scripts.export_openapi → vp run generate:api → commitear ambos." >&2
  exit 1
fi

# scripts/hooks/gitleaks-staged.sh
command -v gitleaks >/dev/null || { echo "Falta gitleaks: brew install gitleaks (ver README «Calidad y tests»)" >&2; exit 1; }
exec gitleaks git --pre-commit --staged --redact --verbose   # imprime File y Line de cada hallazgo

# scripts/hooks/commit-msg.sh <archivo-del-mensaje>
first="$(head -n1 "$1")"
[[ "$first" =~ ^(Merge|Revert|fixup!|squash!)\  ]] && exit 0     # mensajes que genera git
re='^(feat|fix|chore|docs|refactor|test|perf|ci|build)(\([a-z0-9-]+\))?!?: .+$'
if [[ ! "$first" =~ $re ]] || (( ${#first} > 72 )); then
  echo "Mensaje inválido: «$first»" >&2
  echo "Formato: <tipo>(<scope>)?: <descripción>, primera línea de hasta 72 caracteres." >&2
  echo "Tipos: feat|fix|chore|docs|refactor|test|perf|ci|build. Ejemplo: feat(backend): agrega Clock inyectable" >&2
  exit 1
fi
```

`${#first}` cuenta caracteres (no bytes) porque los scripts exportan `LC_ALL=C.UTF-8` (o `en_US.UTF-8` en macOS) al inicio.

Se instala con `brew install lefthook gitleaks` (o `uv tool install lefthook`) y luego `lefthook install` (AC-8). `stage_fixed: true` re-stagea solo los archivos que ya estaban stageados; los cambios de formato sobre archivos no stageados quedan en el working tree.

## Backend changes

**`backend/pyproject.toml`**:

```toml
dependencies = [ # se agregan
  "alembic>=1.14", "structlog>=25.1", "asgi-correlation-id>=4.3",
]
[dependency-groups]
dev = ["ruff>=0.8", "mypy>=1.13", "pytest>=8.3", "pytest-asyncio>=0.24", "httpx>=0.27",
       "import-linter>=2.1", "pytest-cov>=6.0", "pytest-randomly>=3.16", "hypothesis>=6.120",
       "schemathesis>=4.0", "testcontainers[postgres]>=4.9"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "N", "SIM", "RUF", "ANN"]
extend-select = ["ASYNC", "FAST", "S", "DTZ", "BLE", "TRY", "T20", "ERA", "PT", "PIE", "RET", "C4",
                 "PTH", "LOG", "G", "PERF", "TC", "ARG", "FURB", "TID", "PL", "C90", "FBT"]   # AC-23
ignore = [
  "PLR2004", # números mágicos: ruido en límites HTTP y tests; los umbrales de dominio van en constantes con nombre
  "TRY003",  # mensajes largos en excepciones: los usamos para el `detail` de RFC 9457
  "FBT003",  # booleanos posicionales en llamadas a librerías (SQLAlchemy, FastAPI) que no controlamos
]
[tool.ruff.lint.mccabe]
max-complexity = 10
[tool.ruff.lint.flake8-type-checking]
# TC movería a `if TYPE_CHECKING:` imports que Pydantic, FastAPI y SQLAlchemy evalúan en runtime.
runtime-evaluated-base-classes = ["pydantic.BaseModel", "pydantic_settings.BaseSettings", "app.db.base.Base"]
runtime-evaluated-decorators = ["fastapi.APIRouter.get", "fastapi.APIRouter.post", "fastapi.APIRouter.put",
                                "fastapi.APIRouter.patch", "fastapi.APIRouter.delete"]
[tool.ruff.lint.flake8-tidy-imports.banned-api]                                            # AC-24
"datetime.datetime.utcnow".msg = "Usá datetime.now(UTC) o el Clock inyectable."
"requests".msg = "Usá httpx.AsyncClient: requests bloquea el event loop."
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "PLR2004", "ARG001"] # assert, literales y fixtures sin usar son idiomáticos en pytest
"migrations/**" = ["ERA001"]               # Alembic genera comentarios de código

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "-m 'not db' --cov=app --cov-branch --cov-report=term-missing"
filterwarnings = ["error"]                                                                   # AC-33
markers = ["db: requiere PostgreSQL real vía testcontainers (scripts/gate.sh migrations)"]

[tool.coverage.run]
branch = true
source = ["app"]
omit = ["app/__main__.py", "app/scripts/*"]
[tool.coverage.report]
fail_under = 85                                                                             # Resolved Decisions
show_missing = true

[tool.importlinter]                                                                         # AC-20 a AC-22
root_package = "app"
include_external_packages = true
[[tool.importlinter.contracts]]
name = "Capas"
type = "layers"
layers = ["app.scripts", "app.main", "app.api", "app.services", "app.db | app.schemas", "app.domain", "app.core"]
[[tool.importlinter.contracts]]
name = "Dominio puro"
type = "forbidden"
source_modules = ["app.domain"]
forbidden_modules = ["fastapi", "sqlalchemy", "httpx", "matriz_client"]
[[tool.importlinter.contracts]]
name = "API sin acceso directo a la DB"
type = "forbidden"
source_modules = ["app.api"]
forbidden_modules = ["app.db", "sqlalchemy"]
allow_indirect_imports = true
# Con include_external_packages, import-linter registra el paquete externo de primer nivel (`sqlalchemy`),
# no el submódulo: la excepción se escribe contra `sqlalchemy`.
ignore_imports = ["app.api.deps -> app.db.session", "app.api.deps -> sqlalchemy"]
```

`test_tooling.py` (AC-25) agrega, sin tocar `test_ann_rules_enabled_without_exceptions`:

```python
REQUIRED_RUFF_GROUPS: Final = {"ASYNC", "FAST", "S", "DTZ", "BLE", "TRY", "T20", "ERA", "PT", "PIE", "RET", "C4",
                               "PTH", "LOG", "G", "PERF", "TC", "ARG", "FURB", "TID", "PL", "C90", "FBT"}
REQUIRED_CONTRACTS: Final = {"Capas", "Dominio puro", "API sin acceso directo a la DB"}

def test_ruff_groups_enabled() -> None: ...        # REQUIRED_RUFF_GROUPS ⊆ select ∪ extend-select
def test_ruff_ignores_are_justified() -> None: ... # cada línea de `ignore` en pyproject.toml lleva `# ` con texto
def test_import_contracts_present() -> None: ...   # nombres de [[tool.importlinter.contracts]] ⊇ REQUIRED_CONTRACTS
def test_coverage_threshold() -> None: ...         # [tool.coverage.report].fail_under >= 85
```

**`app/domain/numeric.py`** (AC-51, AC-53):

```python
DECIMAL_CONTEXT: Final = Context(prec=28, rounding=ROUND_HALF_EVEN)
_as_str = PlainSerializer(str, return_type=str, when_used="json")

Price    = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=8), _as_str]
Quantity = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=8), _as_str]
Money    = Annotated[Decimal, Field(max_digits=24, decimal_places=8), _as_str]

def round_to_tick(price: Decimal, tick: Decimal) -> Decimal:
    """Redondea `price` al múltiplo de `tick` más cercano (ROUND_HALF_EVEN). Lanza ValueError si `tick` <= 0."""
    if tick <= 0:
        raise ValueError(f"tick debe ser > 0, recibido {tick}")
    steps = (price / tick).quantize(Decimal(1), rounding=ROUND_HALF_EVEN, context=DECIMAL_CONTEXT)
    return (steps * tick).quantize(tick, context=DECIMAL_CONTEXT)
```

Propiedades de `tests/test_numeric.py` (AC-53), todas con `@settings(max_examples=200)` y `st.decimals(allow_nan=False, allow_infinity=False, places=8)`:
- `round_to_tick(round_to_tick(p, t), t) == round_to_tick(p, t)` (idempotencia).
- `a + b == b + a` para `Money` (conmutatividad).
- `TypeAdapter(Money).validate_json(TypeAdapter(Money).dump_json(m)) == m` y el JSON es un string (sin pérdida de precisión).

**`app/core/clock.py`** (AC-54):

```python
class Clock(Protocol):
    def now(self) -> datetime: ...

class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

def get_clock() -> Clock:
    return SystemClock()
```

**`app/api/deps.py`**:
`SessionDep = Annotated[AsyncSession, Depends(get_session)]` y `ClockDep = Annotated[Clock, Depends(get_clock)]`. En los tests se reemplaza con `app.dependency_overrides[get_clock]`.

**Errores RFC 9457** (AC-48):

```python
# app/schemas/problem.py
class ValidationIssue(BaseModel):
    loc: list[str | int]
    msg: str
    type: str

class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    correlation_id: str | None = None
    errors: list[ValidationIssue] | None = None

# app/domain/errors.py
class DomainError(Exception):
    status: ClassVar[int] = 422
    title: ClassVar[str] = "Regla de dominio violada"
    def __init__(self, detail: str) -> None: ...

# app/api/errors.py
PROBLEM_MEDIA_TYPE: Final = "application/problem+json"
_PROBLEM_CONTENT: Final = {PROBLEM_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}
# `model` registra el componente y publica application/json (lo que tipa Orval); `content` agrega
# application/problem+json para que Schemathesis acepte el Content-Type real de la respuesta.
PROBLEM_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    404: {"model": ProblemDetails, "content": _PROBLEM_CONTENT, "description": "No encontrado (RFC 9457)"},
    422: {"model": ProblemDetails, "content": _PROBLEM_CONTENT, "description": "Validación (RFC 9457)"},
    500: {"model": ProblemDetails, "content": _PROBLEM_CONTENT, "description": "Error interno (RFC 9457)"},
}
def register_exception_handlers(app: FastAPI) -> None:
    """starlette HTTPException, RequestValidationError, DomainError y Exception → ProblemDetails con PROBLEM_MEDIA_TYPE."""
```

Mapeo de cada handler (AC-48):

| Excepción | `status` | `title` | `detail` | `errors` |
|---|---|---|---|---|
| `starlette.exceptions.HTTPException` (cubre la de FastAPI y los 404/405 de routing) | `exc.status_code` | `HTTPStatus(status).phrase` | `exc.detail` si es `str` | `None` |
| `RequestValidationError` | `422` | `"Validación fallida"` | `"El request no cumple el esquema"` | `[ValidationIssue(loc, msg, type)]` de `exc.errors()` |
| `DomainError` (y subclases) | `exc.status` | `exc.title` | `exc.detail` | `None` |
| `Exception` | `500` | `"Error interno"` | `None` (nunca el traceback) | `None` |

En todos: `instance = request.url.path`, `correlation_id = asgi_correlation_id.correlation_id.get()`, `type = "about:blank"`. El handler de `Exception` loguea con `exc_info` y agrega a mano el header `X-Request-ID`: Starlette lo atiende en `ServerErrorMiddleware`, por fuera de `CorrelationIdMiddleware`.

**Observabilidad** (AC-46, AC-47, AC-50):

```python
# app/core/logging.py
SENSITIVE_KEY: Final = re.compile(r"password|token|secret|api_key", re.IGNORECASE)
def redact_sensitive(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Reemplaza por "***" los valores SecretStr y los de claves que matchean SENSITIVE_KEY, también anidados."""
def configure_logging(app_env: Literal["development", "production"], log_level: str) -> None:
    """structlog + stdlib (uvicorn, sqlalchemy) vía ProcessorFormatter. JSONRenderer en production, ConsoleRenderer en otro caso."""
```

`app/main.py` → `create_app()` sigue sin leer `Settings`:

```python
# El último add_middleware es el más externo: CorrelationId envuelve a AccessLog, así el log de acceso ya tiene el id.
app.add_middleware(AccessLogMiddleware)            # app/api/middleware.py: event="request", method, path, status, duration_ms
app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")   # valida UUID4; si es inválido, genera uno (AC-47)
register_exception_handlers(app)
# lifespan: configure_logging(settings.app_env, settings.log_level) antes de crear el engine
```

`structlog.contextvars.merge_contextvars` está en la cadena de procesadores; `AccessLogMiddleware` hace `bind_contextvars(correlation_id=correlation_id.get())` al entrar y `clear_contextvars()` al salir, así todo log emitido dentro del request lleva `correlation_id` (AC-46). `app/__main__.py:17` llama `uvicorn.run(..., log_config=None, access_log=False)`: sin `log_config=None`, uvicorn reaplica su `dictConfig` y pisa la configuración de structlog.

**Alembic** (AC-40):
- Se crea con `uv run alembic init -t async migrations` desde `backend/`.
- `migrations/env.py` usa `target_metadata = Base.metadata` y resuelve la URL así: `url = config.get_main_option("sqlalchemy.url") or str(load_settings().database_url)`. La opción explícita gana para que `test_migrations.py` apunte al contenedor; en uso normal sale de `Settings`.
- `alembic.ini` no tiene URL.
- `file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s`.

**Tests nuevos**:
- `test_contract.py` (AC-34):
  ```python
  schema = schemathesis.openapi.from_path(BACKEND_DIR / "openapi.json")   # el archivo versionado, no /api/openapi.json

  @schema.parametrize()
  def test_api_cumple_contrato(case: schemathesis.Case) -> None:
      case.call_and_validate(app=create_app())   # transporte ASGI en proceso, sin lifespan ni DB
  ```
  T1 fija la firma exacta del transporte ASGI en la versión 4.x instalada (`app=` en `call_and_validate` o `schema.app`). Las rutas que usan `SessionDep` se excluyen con `schema.exclude(...)` hasta que haya fixture de DB; hoy no hay ninguna.
- `test_migrations.py` (AC-35, AC-41): todo el módulo con `pytestmark = pytest.mark.db`. Fixture de módulo `PostgresContainer("postgres:17", driver="psycopg")`; `cfg = Config(BACKEND_DIR / "alembic.ini")`, `cfg.set_main_option("sqlalchemy.url", container.get_connection_url())`; corre `command.upgrade(cfg, "head")` y `command.check(cfg)`. Si Docker no está disponible, el test **falla** (no se saltea): en el gate `migrations` Docker es un prerrequisito.
- `test_domain_types.py` (AC-52):
  - Recorre `pkgutil.walk_packages(app.schemas.__path__)` (todas las subclases de `BaseModel`) y `Base.metadata.tables`.
  - Nombres monetarios: `MONEY_FIELD: Final = re.compile(r"price|qty|quantity|amount|notional|money|pnl|balance", re.I)`.
  - En esquemas, el tipo del campo (desenvuelto de `Annotated`/`Optional`) debe ser `Decimal`. En el ORM, la columna debe ser `Numeric` con `precision` y `scale` no nulos y `asdecimal=True`.
  - El mensaje de falla es `"<Modelo>.<campo>: <tipo encontrado>"`.
  - La función de chequeo recibe la lista de modelos, así el mismo test la ejerce con un modelo probe (`price: float`) y con una tabla probe (`Column("amount", Float)` en una `MetaData` aislada), y exige que ambos sean detectados.

## Frontend changes

**`frontend/package.json`**:
- devDependencies nuevas: `dependency-cruiser`, `knip`, `@vitest/coverage-v8`, `@axe-core/playwright`, `size-limit`, `@size-limit/file`, `msw` y `@faker-js/faker`.
- Bloques y scripts:

```json
"scripts": {
  "generate:api": "orval --config orval.config.ts",
  "e2e": "playwright test",
  "lint:arch": "depcruise src --config .dependency-cruiser.cjs",
  "lint:unused": "knip",
  "size": "size-limit"
},
"size-limit": [{ "name": "JS total (gzip)", "path": "dist/assets/*.js", "gzip": true, "limit": "<ver regla abajo>" }]
```

Regla del límite (AC-39): en T14 se mide `vp build && vp run size`, se suma 10 % y se redondea hacia arriba al múltiplo de 5 kB siguiente. Subir el límite después exige justificarlo en el PR.

**`frontend/knip.config.ts`** (AC-31). Va en TS, y no en `package.json`, para que cada excepción lleve su comentario (NFR «Bloqueante desde el día 1»):

```ts
import type { KnipConfig } from "knip";

const config: KnipConfig = {
  entry: ["src/main.tsx", "e2e/**/*.spec.ts", "src/test/setup.ts"],
  project: ["src/**/*.{ts,tsx}", "e2e/**/*.ts"],
  ignore: ["src/api/generated/**"], // salida de Orval: no se edita a mano
  ignoreDependencies: [
    "@faker-js/faker", // solo lo importan los *.msw.ts generados, que están en `ignore`
  ],
};
export default config;
```

T3 agrega a `ignoreDependencies` cualquier otro falso positivo que knip reporte (p. ej. paquetes que solo carga `vp`), cada uno con su comentario; nunca código propio sin usar.

**`frontend/vite.config.ts`**, bloque `lint` (AC-26 a AC-28). Los nombres exactos de las reglas y el comportamiento de los overrides se confirman en T1:

```ts
const RESTRICTED_IMPORTS = [
  { group: ["../../*", "../../**"], message: "Usá el alias @/ (frontend/CLAUDE.md, reglas de dependencia)." },
  { group: ["axios"], message: "El backend se consume solo vía el cliente Orval (frontend/CLAUDE.md, acceso al backend)." },
];
lint: {
  plugins: ["react", "typescript", "oxc", "jsx-a11y", "import", "vitest", "promise", "unicorn"],
  // Sin `warn`: un warning no corta `vp check` y el NFR exige gates bloqueantes.
  categories: { correctness: "error", suspicious: "error", perf: "error" },
  ignorePatterns: ["src/api/generated/**", "dist/**", "coverage/**"],
  rules: {
    "react/rules-of-hooks": "error",
    "react/exhaustive-deps": "error",
    "react/only-export-components": ["error", { allowConstantExport: true }],
    "react/no-danger": "error",
    "typescript/no-explicit-any": "error",
    "typescript/no-non-null-assertion": "error",
    "typescript/no-floating-promises": "error",
    "typescript/ban-ts-comment": ["error", { "ts-expect-error": "allow-with-description" }],
    "no-console": "error",
    "import/no-cycle": "error",
    "no-restricted-globals": ["error", { name: "fetch", message: "fetch solo en src/api/mutator.ts; usá el cliente Orval." }],
    "no-restricted-imports": ["error", { patterns: RESTRICTED_IMPORTS }],
    "vite-plus/prefer-vite-plus-imports": "error",
  },
  overrides: [
    // Única excepción de §5: el mutator es el punto de fetch. Con MSW, los tests ya no tocan `fetch`.
    { files: ["src/api/mutator.ts"], rules: { "no-restricted-globals": "off" } },
  ],
  options: { typeAware: true, typeCheck: true },
  jsPlugins: [{ name: "vite-plus", specifier: "vite-plus/oxlint-plugin" }],
},
test: {
  environment: "jsdom",
  setupFiles: ["./src/test/setup.ts"],
  include: ["src/**/*.test.{ts,tsx}"],
  css: false,
  coverage: {                                                                     // AC-36
    provider: "v8",
    include: ["src/**/*.{ts,tsx}"],
    // Definir `exclude` reemplaza los defaults de Vitest: los archivos de test se excluyen a mano.
    exclude: ["src/api/generated/**", "src/test/**", "e2e/**", "src/**/*.test.{ts,tsx}", "src/main.tsx", "src/vite-env.d.ts"],
    thresholds: { lines: 70, branches: 70, functions: 70, statements: 70 },     // Resolved Decisions
  },
},
```

El `enum` (AC-28) ya lo rechaza TypeScript por `erasableSyntaxOnly` (TS1294) dentro de `vp check`. El probe de `verify-guards.sh` lo confirma.

`no-restricted-globals` no detecta `window.fetch` ni `globalThis.fetch`. T1 verifica si el Oxlint de `vp` soporta `no-restricted-properties`; si lo soporta, se agrega `{ object: "window" | "globalThis", property: "fetch" }` con el mismo mensaje; si no, queda registrado en Critical Decisions como hueco conocido (AC-27).

**`frontend/.dependency-cruiser.cjs`** (AC-29, AC-30):

```js
module.exports = {
  forbidden: [
    { name: "no-circular", severity: "error", from: {}, to: { circular: true } },
    { name: "screen-no-otra-screen", severity: "error",
      from: { path: "^src/screens/([^/]+)/" }, to: { path: "^src/screens/", pathNot: "^src/screens/$1/" } },
    { name: "components-limites", severity: "error",
      from: { path: "^src/components/" }, to: { path: "^src/(screens|api|stores|layouts)/" } },
    { name: "hooks-limites", severity: "error",
      from: { path: "^src/hooks/" }, to: { path: "^src/(screens|components|layouts)/" } },
    { name: "utils-constants-puros", severity: "error",
      from: { path: "^src/(utils|constants)/" },
      to: { pathNot: "^src/(types|utils|constants)/", dependencyTypes: ["local", "aliased", "npm", "npm-dev"] } },
    { name: "screen-via-index", severity: "error",
      from: { pathNot: "^src/(screens|app)/" }, to: { path: "^src/screens/[^/]+/(?!index\\.ts$)" } },
  ],
  options: { tsConfig: { fileName: "tsconfig.json" }, doNotFollow: { path: "node_modules" },
             exclude: { path: "^src/api/generated/" } },
};
```

**`frontend/tsconfig.json:21` y `frontend/tsconfig.node.json:17`** (AC-32): se agregan `"exactOptionalPropertyTypes": true`, `"noPropertyAccessFromIndexSignature": true` y `"noImplicitReturns": true` en ambos. `verbatimModuleSyntax`, `noUnusedLocals`, `noUnusedParameters` y `noFallthroughCasesInSwitch` ya están activos en los dos (`tsconfig.json:11-20`, `tsconfig.node.json:10-17`).

**Mutator** (AC-49):

```ts
import type { ProblemDetails } from "@/api/generated/model";

export class ApiError<TBody = unknown> extends Error {
  readonly status: number;
  readonly body: TBody;
  readonly title: string | undefined;
  readonly detail: string | undefined;
  readonly correlationId: string | undefined;
  constructor(status: number, body: TBody) {
    const problem = isProblemDetails(body) ? body : undefined;
    super(problem?.title ?? `HTTP ${status}`);   // el message deja de ser genérico cuando hay ProblemDetails
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.title = problem?.title;
    this.detail = problem?.detail ?? undefined;          // el backend manda `null`; se normaliza a undefined
    this.correlationId = problem?.correlation_id ?? undefined;
  }
}
export const isProblemDetails = (body: unknown): body is ProblemDetails =>
  typeof body === "object" && body !== null && "title" in body && "status" in body;
```

`parseBody` (`mutator.ts:21`) no cambia: `application/problem+json` contiene `json` y ya se parsea. Si el cuerpo de error no es `ProblemDetails` (p. ej. un 502 HTML de nginx), `title`, `detail` y `correlationId` quedan `undefined` y `message` es `HTTP <status>`.

**MSW** (Resolved Decisions):
- `orval.config.ts` → `output.mock: true`, que genera `generated/<tag>/<tag>.msw.ts`.
- `src/test/server.ts` exporta `server = setupServer()`.
- `src/test/setup.ts` registra `beforeAll(() => server.listen({ onUnhandledRequest: "error" }))`, `afterEach(() => server.resetHandlers())` y `afterAll(() => server.close())`, importando `beforeAll`/`afterAll`/`afterEach` de `vite-plus/test` (regla `vite-plus/prefer-vite-plus-imports`).
- El `customFetch` usa URLs relativas (`BASE_URL = ""`); en jsdom se resuelven contra `location.origin`, así que los handlers usan `*/api/...`.
- Los tests registran handlers con `server.use(getGetHealthMockHandler({...}))` o `http.get("*/api/health", () => HttpResponse.json(problem, { status: 500, headers: { "content-type": "application/problem+json" } }))`.

**`src/utils/format.ts`** (AC-57):

```ts
const LOCALE = "es-AR";
const cache = new Map<string, Intl.NumberFormat>();
const formatter = (min: number, max: number): Intl.NumberFormat => { /* cachea por `${min}:${max}` */ };
/** `value` es el string decimal de la API; Intl lo formatea sin pasar por float. */
export const formatPrice = (value: string, decimals: number): string => formatter(decimals, decimals).format(value as Intl.StringNumericLiteral);
export const formatQuantity = (value: string, maxDecimals: number): string => formatter(0, maxDecimals).format(value as Intl.StringNumericLiteral);
```

El `as Intl.StringNumericLiteral` se justifica en un comentario: la API garantiza strings decimales (AC-51). `formatter` usa `{ minimumFractionDigits: min, maximumFractionDigits: max, roundingMode: "halfEven" }` para coincidir con `ROUND_HALF_EVEN` del backend. Un string no numérico produce `"NaN"` de `Intl`; los formatters no validan, porque el contrato de la API ya lo garantiza.

**`e2e/a11y.spec.ts`** (AC-37): mockea `/api/health` igual que `home.spec.ts`, y en `/` y `/no-existe` exige que `new AxeBuilder({ page }).withTags(["wcag2a","wcag2aa","wcag21aa","wcag22aa"]).analyze()` devuelva `violations` igual a `[]`.

## Docs y steering

- **`CLAUDE.md` raíz** (200 líneas o menos, AC-59). Contiene:
  - §1 Contexto (con el producto: trading manual asistido y algorítmico).
  - §2 Stack, en tabla corta.
  - §3 Comandos: `scripts/gate.sh` como entrada principal.
  - §4 Gates y dónde corren: tabla de quick/full por consumidor.
  - §5 Definición de terminado: `scripts/gate.sh changed full` más e2e si aplica.
  - §6 Checklist.
  - Remisión a `backend/CLAUDE.md` y `frontend/CLAUDE.md`.
- **`backend/CLAUDE.md`**:
  - Las secciones actuales de estructura, convenciones y tests del backend.
  - Capas (import-linter), tipos de dominio, `Clock`, errores RFC 9457, logging, Alembic con `alembic check` y Squawk.
  - Las **reglas obligatorias para la primera feature de órdenes** de AC-55.
  - Cada regla automatizada termina con «— lo verifica `<herramienta>`» (AC-60).
- **`frontend/CLAUDE.md`**:
  - Estructura y reglas de dependencia (`lint:arch`), Orval, estado, navegación, AntD, TS y componentes.
  - Tests con MSW (reemplaza la §8 actual).
  - Las reglas de UI de órdenes de AC-56.
- **`.octo/steering/*.md`** (AC-58):
  - `product.md`: propósito, usuarios (trader manual y operador de estrategias), objetivos y no-objetivos.
  - `tech.md`: stack y `scripts/gate.sh`.
  - `structure.md`: capas del backend y del frontend, y dónde va el código nuevo.
- **`README.md` §Calidad y tests** (AC-7): instalar lefthook y gitleaks, uso de `scripts/gate.sh`, secret `MARKET_LIBS_TOKEN` (cómo crear la GitHub App o el PAT), aplicar el ruleset con `gh api` y Renovate (instalar la app con acceso a `matriz-trader` y `market-libs`).
- **`.github/pull_request_template.md`** (AC-61).

## Key implementation details

- **quick y full** (AC-19):
  - `quick` es un subconjunto de `full` y corre en lefthook, porque un `pre-commit` de minutos invita a usar `--no-verify`.
  - `full` es lo que corren Stop, Octo y CI.
  - Ambos modos viven solo en `scripts/gate.sh`.
- **Los tests `db` quedan fuera del gate `backend`:**
  - `addopts` tiene `-m 'not db'` para que Stop y lefthook no dependan de Docker.
  - Esos tests corren en el target `migrations`, local y en CI igual: testcontainers con el Docker disponible (sin service container, para que local y CI sean idénticos).
  - `pytest -m db` pisa el `-m 'not db'` de `addopts` (pytest usa el último `-m`), y `--no-cov` evita que el umbral de cobertura se calcule sobre ese subconjunto.
- **`create_app()` sigue sin leer `Settings`:** los middlewares y handlers no necesitan configuración, y `configure_logging` corre en el `lifespan` y en `__main__`. Los tests con `ASGITransport` siguen sin necesitar `.env`.
- **Errores tipados por Orval:** el OpenAPI declara `ProblemDetails` en `404`, `422` y `500` con `responses=` a nivel de `api_router` (`router.py:7`), que FastAPI copia a cada ruta del OpenAPI (AC-48). Cada respuesta lista `application/json` (de `model`, lo que usa Orval para tipar) y `application/problem+json` (de `content`, el Content-Type real, que Schemathesis valida). El mutator parsea ambos porque contienen `json`.
- **`changed` vs `branch`:** el hook `Stop` usa `changed` (AC-16 habla de cambios sin commitear); Octo usa `branch` porque puede commitear por tarea (AC-18). CI no usa ninguno: corre cada módulo según el filtro de rutas.
- **Orden dentro de cada gate:** de lo más barato a lo más caro (formato → lint → tipos → arquitectura → tests → build → probes), y se corta en el primer fallo del módulo (`&&`).
- **Fallas de entorno:** si falta `uv`, `vp`, `jq`, `gitleaks` o Docker (solo `migrations`), el script correspondiente sale con código distinto de 0 y un mensaje que nombra la herramienta; ningún gate se saltea en silencio.
- **Probes de `verify-guards.sh`:** se escriben dentro del módulo, porque las herramientas resuelven config y alias desde ahí, con nombres `_probe*` y `trap` de borrado. `.gitignore` incluye `**/_probe*` por si queda alguno.
- **Dependencias nuevas, justificadas (§2 de `CLAUDE.md`):** ninguna duplica una responsabilidad de la tabla del stack.
  - import-linter y dependency-cruiser: verificación de arquitectura.
  - knip: código muerto.
  - pytest-cov y coverage-v8: cobertura.
  - hypothesis: propiedades numéricas.
  - schemathesis: contrato.
  - testcontainers: PostgreSQL real.
  - alembic: migraciones (ya anunciado en §6).
  - structlog y asgi-correlation-id: observabilidad.
  - axe: accesibilidad.
  - size-limit: presupuesto de bundle.
  - msw y faker: mocks de red generados por Orval.
  - lefthook y gitleaks: hooks y secretos.
  - Se agregan como filas nuevas a la tabla del stack.

## Risks & rollback

| Risk | Mitigation | How to revert |
|---|---|---|
| Los overrides de Oxlint reemplazan en lugar de combinar `no-restricted-imports`, o `import/no-cycle` no resuelve `@/` | T1 lo prueba. Las reglas de carpetas y los ciclos ya quedan cubiertos por dependency-cruiser (AC-29) | Quitar la regla de Oxlint y dejar solo `lint:arch` |
| `exactOptionalPropertyTypes` rompe tipos generados por Orval o de AntD | T1 corre `vp check` con el flag. `src/api/generated/` ya está excluido de lint, pero no de TS | Desactivar el flag y registrarlo en Critical Decisions |
| `uv audit` todavía en preview | `scripts/audit.py` usa `pip-audit` sobre `uv export --frozen` si `uv audit` no es estable (T1) | Cambiar el comando dentro de `scripts/audit.py` |
| Renovate no detecta las fuentes git de `[tool.uv.sources]` | `customManagers` de tipo regex (T1) | Actualizar los tags a mano (documentado) |
| Cambiar Ruff genera muchas correcciones en el esqueleto | El esqueleto es chico; `ruff check --fix` más revisión manual en T2 | Revertir el commit de T2 |
| Las reglas `TC` mueven a `TYPE_CHECKING` imports que Pydantic/FastAPI necesitan en runtime | `runtime-evaluated-base-classes` y `runtime-evaluated-decorators` en `pyproject.toml`; `pytest` lo detecta (T2) | Agregar la clase o decorador faltante a esas listas |
| Squawk vía `uvx squawk-cli` no disponible | T1 confirma el paquete; alternativa: binario de release fijado | Cambiar la línea en `migrations_full` |
| knip reporta falsos positivos por paquetes que solo carga `vp` | `ignoreDependencies` con comentario en `knip.config.ts` (T3) | Quitar `lint:unused` de `frontend_full` y registrarlo en Critical Decisions |
| Schemathesis rechaza `application/problem+json` por no estar declarado | `PROBLEM_RESPONSES` declara ambos media types (T5); `test_contract.py` lo prueba (T9) | Quitar `content` y aceptar el check `content_type_conformance` como excepción documentada |
| La organización `gravity-quant` no aprueba PATs fine-grained | Migrar a GitHub App (documentado en README) | Ver Open Questions |
| `vp check --fix` no existe en la versión 1.7 de `vp` | T1 lo verifica; alternativa en `frontend_quick`: `vp fmt && vp lint --fix && vp check` | Cambiar `frontend_quick` en `gate.sh` |
| Un agente escribe archivos protegidos vía `Bash` en lugar de `Edit` | lefthook `generated-sync`, `test_openapi_export.py` y CI | — |
| El hook `Stop` tarda varios minutos en cada turno | Solo corre los módulos con cambios; tiene `timeout` de 900 s y `stop_hook_active` evita loops | Quitar la entrada `Stop` de `.claude/settings.json` |
| El secret `MARKET_LIBS_TOKEN` filtra en logs | Se pasa por `env`, GitHub lo enmascara y `persist-credentials: false`; zizmor audita | Rotar el token |

## Verification

| AC | Cómo se prueba |
|---|---|
| AC-1, AC-2, AC-3, AC-6 | PR de prueba que toca solo `frontend/`: `backend` queda `skipped`, `ci-ok` en verde, cache hit en el segundo run. zizmor y actionlint en verde validan permisos y SHA |
| AC-4, AC-5 | Run con el secret: `uv sync --frozen` instala `market-libs`. Run en un fork sin el secret: el job falla con `Falta el secret MARKET_LIBS_TOKEN` |
| AC-7, AC-61 | Revisión de `README.md` y `.github/pull_request_template.md`. `gh api ... --input .github/rulesets/main.json` aplicado y visible en Settings → Rules |
| AC-8 | `lefthook install` en la raíz crea `.git/hooks/pre-commit` y `.git/hooks/commit-msg` |
| AC-9 | Commit de un `.py` mal formateado: se corrige y re-stagea. Commit con un error de mypy: aborta |
| AC-10 | Commit de un `.tsx` con un import de `screens/` desde `components/`: aborta con `components-limites` |
| AC-11 | Commit de `generated/` sin `openapi.json`: aborta con el mensaje que remite al flujo de contrato |
| AC-12 | Commit de un archivo con un token falso `ghp_` + 36 caracteres: aborta mostrando `File:` y `Line:` |
| AC-13 | `git commit -m wip` aborta con el formato esperado; `git commit -m "feat(backend): ok"` pasa; un merge commit pasa |
| AC-14 | Sesión de Claude Code: pedir editar `frontend/src/api/generated/health/health.ts` y `.env` → bloqueado con el comando de regeneración |
| AC-15 | Escribir un `.py` con `print(...)` → el agente recibe `T201` por stderr |
| AC-16, AC-17 | Terminar el turno con un test roto: el Stop reinyecta la salida del gate; el segundo Stop con `stop_hook_active: true` sale con 0. Además, `echo '{"stop_hook_active":true}' \| .claude/hooks/stop-gate.sh; echo $?` da 0 |
| AC-18 | `grep -c npm .octo/hooks/code-validate-improve.json` da 0. Al cerrar una wave de Octo se ejecuta `scripts/gate.sh branch full` |
| AC-19 | `grep -rnE "ruff (check\|format)\|vp (check\|lint\|fmt\|test)\|pytest\|mypy" .github lefthook.yml .claude .octo/hooks scripts/hooks` no encuentra nada: todos invocan `scripts/gate.sh` |
| AC-20, AC-21, AC-22, AC-25 | `uv run lint-imports` en verde. `verify-guards.sh backend` (probes de dominio y api). `test_tooling.py` falla si se quita un contrato o grupo |
| AC-23, AC-24 | `test_tooling.py` y `verify-guards.sh backend` (probes DTZ003, DTZ005, ASYNC251 y TID251) |
| AC-26, AC-27, AC-28, AC-32 | `vp check` en verde. `verify-guards.sh frontend` (fetch, axios, enum, `../../`). Inspección de `vite.config.ts` y `tsconfig.json` |
| AC-29, AC-30 | `vp run lint:arch` en verde. Probes de pantalla a pantalla, de componente a api y de ciclo fallan con el nombre de la regla |
| AC-31 | `vp run lint:unused` en verde. Un export sin uso agregado a mano hace fallar el comando |
| AC-33 | `uv run pytest` muestra la cobertura de branches y `Required test coverage of 85% reached`. Bajando `fail_under` a 99 falla |
| AC-34 | `uv run pytest tests/test_contract.py` en verde. Cambiar `HealthResponse.status` a `int` en el handler, sin regenerar, hace fallar el test |
| AC-35, AC-40, AC-41 | `scripts/gate.sh migrations full` local con Docker y en el job `migrations`. Agregar un modelo sin migración hace fallar `alembic check` |
| AC-42 | Una migración temporal con `op.add_column(..., nullable=False)` sin default hace fallar Squawk (`adding-required-field`) |
| AC-36 | `vp test run --coverage` en verde con umbrales del 70 % |
| AC-37 | `vp run e2e` en verde. Un `<button>` sin nombre accesible temporal hace fallar `a11y.spec.ts` |
| AC-38 | `frontend/playwright.config.ts:9-14` ya cumple; inspección del paso `upload-artifact` con `if: failure()` en el job `e2e` |
| AC-39 | `vp run size` en verde. Bajar el límite a 1 kB hace fallar mostrando tamaño medido y límite |
| AC-43 | `python3 scripts/audit.py` en verde. Una entrada de allowlist con `expires` pasado hace fallar. Job `security` en verde con `gitleaks` sobre `base..HEAD` |
| AC-44 | Job `workflow-lint` en verde. Un `uses: actions/checkout@v4` sin SHA hace fallar zizmor |
| AC-45 | `npx --yes renovate-config-validator renovate.json` en verde. El primer PR de Renovate agrupa por módulo |
| AC-46, AC-47, AC-50 | `test_logging.py`: el header `X-Request-ID` está en la respuesta, se reutiliza un UUID entrante, el JSON tiene `correlation_id` y `SecretStr`/`password` salen como `***` |
| AC-48 | `test_errors.py`: 404 (ruta inexistente), 422 (endpoint de prueba con parámetro), `DomainError` y `Exception` (endpoints de prueba montados solo en el test) responden `application/problem+json` con `type`, `title`, `status`, `detail`, `instance` y `correlation_id`; el 500 no incluye traceback y trae `X-Request-ID`. `openapi.json` contiene `ProblemDetails` en `GET /api/health` |
| AC-49 | `mutator.test.ts` con MSW: 500 `problem+json` → `ApiError` con `title`, `detail` y `correlationId` |
| AC-51, AC-53 | `test_numeric.py` con Hypothesis (`max_examples=200`): idempotencia de `round_to_tick`, conmutatividad de la suma de `Money` y serialización a string sin pérdida |
| AC-52 | `test_domain_types.py` en verde sobre el esqueleto. El probe con `price: float` declarado en el test es detectado |
| AC-54 | `test_clock.py`: `SystemClock().now().tzinfo is UTC` y el override de `get_clock` en un endpoint de prueba |
| AC-55, AC-56 | Revisión de `backend/CLAUDE.md` (cinco reglas de órdenes) y `frontend/CLAUDE.md` (confirmación, `loading`/`disabled`, strings, formatters) |
| AC-58 | `grep -nE "^- \*\*.*\*\*: *$\|^_Describe\|^_Outline\|^_Document" .octo/steering/*.md` no encuentra nada |
| AC-59 | `wc -l CLAUDE.md` da 200 o menos y el archivo enlaza `backend/CLAUDE.md` y `frontend/CLAUDE.md` |
| AC-60 | `grep -c "lo verifica" CLAUDE.md backend/CLAUDE.md frontend/CLAUDE.md` da más de 0 en cada uno |
| AC-57 | `format.test.ts`: `formatPrice("1234.5", 2)` da `"1.234,50"`, un string de 18 dígitos no pierde precisión y se reutiliza la instancia |
| AC-62 | T22: en un clon limpio, `scripts/gate.sh backend full`, `frontend full`, `e2e full` y `migrations full` salen con 0, con tiempos medidos para los NFR |

## Tasks

### Wave 1
- [ ] T1: Spike de verificación, sin cambios en el repo: overrides de Oxlint y `import/no-cycle` con `@/`, nombres de reglas y soporte de `no-restricted-properties` en el Oxlint de `vp` 1.7, existencia de `vp check --fix`, `exactOptionalPropertyTypes` contra `generated/` y AntD, estado de `uv audit`, versión de `squawk-cli` vía `uvx`, firma del transporte ASGI de Schemathesis 4 y extracción de fuentes git de `[tool.uv.sources]` por Renovate — _outcome: cada incógnita de Risks tiene una entrada con la decisión tomada en Critical Decisions_
- [ ] T2 @backend-expert: Actualizar `backend/pyproject.toml` (dependencias, Ruff ampliado con `flake8-type-checking`, pytest, coverage e import-linter), regenerar `backend/uv.lock`, crear `app/services/__init__.py`, `app/domain/__init__.py` y `app/api/deps.py` con `SessionDep`, corregir las violaciones nuevas y extender `tests/test_tooling.py` — _outcome: `ruff check`, `ruff format --check`, `mypy .`, `lint-imports` y `pytest` (cobertura ≥ 85 %) salen con 0 desde `backend/` (AC-20, AC-22, AC-23, AC-25, AC-33)_
- [ ] T3 @frontend-expert: Agregar a `frontend/package.json` las devDependencies nuevas, los scripts `lint:arch`, `lint:unused` y `size` y el bloque `size-limit`, regenerar `frontend/pnpm-lock.yaml`, crear `frontend/.dependency-cruiser.cjs` y `frontend/knip.config.ts` — _outcome: `vp install`, `vp run lint:arch` y `vp run lint:unused` salen con 0 sobre el esqueleto (AC-29, AC-31)_

### Wave 2 (depends on T1, T2, T3)
- [ ] T4 @backend-expert: Crear `app/domain/numeric.py` y `app/core/clock.py`, agregar `ClockDep` a `app/api/deps.py` y escribir `tests/test_numeric.py`, `tests/test_clock.py` y `tests/test_domain_types.py` — _outcome: `uv run pytest` pasa con las tres propiedades de Hypothesis a 200 ejemplos y con el modelo y la tabla probe detectados (AC-51, AC-52, AC-53, AC-54)_
- [ ] T5 @backend-expert: Implementar errores RFC 9457 (`app/schemas/problem.py`, `app/domain/errors.py`, `app/api/errors.py`, `PROBLEM_RESPONSES` en `app/api/router.py:7` y `register_exception_handlers` en `app/main.py:40`), regenerar `backend/openapi.json` y agregar `tests/test_errors.py` — _outcome: `uv run pytest` en verde con 404, 422, `DomainError` y 500 en `application/problem+json`, y `openapi.json` declara `ProblemDetails` (AC-48)_
- [ ] T6 @database-expert: Inicializar Alembic async (`backend/alembic.ini`, `backend/migrations/**`) con `Base.metadata` y la URL resuelta desde la opción o `Settings`, y crear `tests/test_migrations.py` marcado `db` con testcontainers — _outcome: con Docker, `uv run pytest -m db --no-cov` corre `upgrade head` y `alembic check` en verde (AC-35, AC-40, AC-41)_
- [ ] T7 @frontend-expert: Ampliar los bloques `lint` y `test.coverage` de `frontend/vite.config.ts`, agregar los tres flags a `frontend/tsconfig.json` y `frontend/tsconfig.node.json` y corregir las violaciones en `src/` — _outcome: `vp check` sin errores ni warnings y `vp test run --coverage` sobre el 70 % salen con 0 (AC-26, AC-27, AC-28, AC-32, AC-36)_

### Wave 3 (depends on T4, T5, T6, T7)
- [ ] T8 @backend-expert: Implementar observabilidad: `app/core/logging.py`, `app/api/middleware.py`, `CorrelationIdMiddleware` y `configure_logging` en `app/main.py`, `log_config=None` en `app/__main__.py:17`, y `tests/test_logging.py` — _outcome: `uv run pytest` en verde con `X-Request-ID` generado y reutilizado, `correlation_id` en el JSON y secretos como `***` (AC-46, AC-47, AC-50)_
- [ ] T9 @backend-expert: Crear `backend/tests/test_contract.py` con Schemathesis contra la app ASGI y el `openapi.json` versionado — _outcome: `uv run pytest` en verde y un desvío de contrato provocado a mano hace fallar el test (AC-34)_
- [ ] T10 @frontend-expert: Activar `mock: true` en `frontend/orval.config.ts`, regenerar `src/api/generated/`, crear `src/test/server.ts`, registrar el ciclo de MSW en `src/test/setup.ts` y migrar `HomeScreen.test.tsx` de `vi.stubGlobal` a handlers de MSW — _outcome: `vp test run --coverage` en verde y `grep -rn stubGlobal frontend/src` no encuentra nada (Resolved Decisions)_
- [ ] T11 @frontend-expert: Crear `src/utils/format.ts` y `src/utils/format.test.ts` — _outcome: `vp test run` pasa con `formatPrice("1234.5", 2) === "1.234,50"`, un string de 18 dígitos sin pérdida e instancias cacheadas (AC-57)_
- [ ] T12 @frontend-expert: Crear `frontend/e2e/a11y.spec.ts` con axe sobre Home y 404, corrigiendo las violaciones que aparezcan en `src/screens/*/*.tsx` o `src/layouts/` — _outcome: `vp run e2e` sale con 0 y sin violaciones WCAG 2.2 AA (AC-37, AC-38)_

### Wave 4 (depends on T10)
- [ ] T13 @frontend-expert: Extender `ApiError` en `src/api/mutator.ts` con `title`, `detail` y `correlationId` desde `ProblemDetails`, y crear `src/api/mutator.test.ts` con handlers MSW — _outcome: `vp test run` pasa con un 500 `problem+json` convertido en `ApiError` con los tres campos y un 502 no-JSON con los tres en `undefined` (AC-49)_

### Wave 5 (depends on T8, T9, T11, T12, T13)
- [ ] T14: Crear `scripts/gate.sh`, `scripts/verify-guards.sh` y `scripts/guard-probes/**`, medir el bundle para fijar el límite de `size-limit` en `frontend/package.json` y agregar `**/_probe*`, `coverage/`, `.coverage`, `htmlcov/` y `.hypothesis/` a `.gitignore` — _outcome: `scripts/gate.sh backend full` y `scripts/gate.sh frontend full` salen con 0, lo que incluye que cada probe hace fallar su herramienta con el id esperado (AC-19, AC-21, AC-22, AC-24, AC-27, AC-28, AC-30, AC-39)_

### Wave 6 (depends on T14)
- [ ] T15: Crear `lefthook.yml` y `scripts/hooks/{check-generated-sync,gitleaks-staged,commit-msg}.sh` — _outcome: los escenarios de AC-8 a AC-13 de Verification se comportan como se espera (AC-8, AC-9, AC-10, AC-11, AC-12, AC-13)_
- [ ] T16: Crear `.claude/settings.json` y `.claude/hooks/{guard-paths,fmt-lint-file,stop-gate}.sh`, y actualizar `instructions` en `.octo/hooks/code-validate-improve.json:10` — _outcome: los escenarios de AC-14 a AC-18 de Verification se cumplen en una sesión de Claude Code (AC-14, AC-15, AC-16, AC-17, AC-18)_
- [ ] T17: Crear `.github/workflows/ci.yml` con los jobs `changes`, `backend`, `frontend`, `e2e`, `migrations`, `security`, `workflow-lint` y `ci-ok` — _outcome: actionlint y zizmor en verde localmente y el primer PR muestra todos los jobs con `ci-ok` en verde (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-38, AC-41, AC-42, AC-44)_
- [ ] T18: Crear `scripts/audit.py` y `security-allowlist.toml` — _outcome: `python3 scripts/audit.py` sale con 0 y con 1 si se agrega una entrada vencida (AC-43)_
- [ ] T19: Crear `renovate.json` — _outcome: `npx --yes --package renovate -- renovate-config-validator renovate.json` sale con 0 (AC-45)_
- [ ] T20: Crear `.github/pull_request_template.md` y `.github/rulesets/main.json` — _outcome: un PR nuevo contra `main` se abre con la plantilla y, una vez aplicado el ruleset con `gh api`, exige `ci-ok` (AC-7, AC-61)_

### Wave 7 (depends on T15, T16, T17, T18, T19, T20)
- [ ] T21 @docs-expert: Dividir `CLAUDE.md` en la raíz, `backend/CLAUDE.md` y `frontend/CLAUDE.md`, completar `.octo/steering/{product,tech,structure}.md` y actualizar la sección «Calidad y tests» de `README.md:145` (lefthook, gitleaks, `scripts/gate.sh`, `MARKET_LIBS_TOKEN`, ruleset y Renovate) — _outcome: los chequeos de AC-55 a AC-60 de Verification pasan (AC-7, AC-55, AC-56, AC-58, AC-59, AC-60)_

### Wave 8 (depends on T21)
- [ ] T22: En un clon limpio, seguir el README, instalar lefthook, ejecutar `scripts/gate.sh` con `backend`, `frontend`, `e2e` y `migrations` en modo full, y recorrer la tabla Verification midiendo `pre-commit`, `PostToolUse` y CI — _outcome: todos los gates salen con 0, los tiempos cumplen los NFR y cualquier desvío queda registrado en Critical Decisions (AC-62)_

## Open Questions

Las cuatro preguntas de requirements están resueltas. Defaults tomados en este plan que conviene revisar:

- [ ] ¿Quién crea y rota el acceso de CI a `gravity-quant/market-libs`? Default: PAT fine-grained de 90 días en `MARKET_LIBS_TOKEN`. Si la organización no permite PATs fine-grained o prefiere no depender de una cuenta personal, se pasa a GitHub App (requiere un admin de `gravity-quant`).
- [ ] ¿Quién instala la app de Renovate con acceso a `matriz-trader` y `market-libs`? Sin acceso a `market-libs`, AC-45 queda configurado pero Renovate no puede seguir los tags.
- [ ] `required_approving_review_count: 0` en el ruleset: hoy hay un solo mantenedor. Si se suma otra persona, subirlo a 1.

Las incógnitas técnicas las resuelve T1 y se registran en Critical Decisions.

## Critical Decisions
### Critical Decision — T2: `FAST001` reemplaza a `response_model` explícito
- **What**: se quitó `response_model=HealthResponse` de `app/api/routes/health.py`; FastAPI toma el esquema de la anotación de retorno (`-> HealthResponse`) y `openapi.json` no cambia (`test_openapi_export.py` en verde).
- **Why**: AC-23 exige `FAST001` activo y esa regla marca como redundante un `response_model` igual al tipo de retorno; un `noqa` en cada ruta sería ruido permanente.
- **Affects**: la regla de §6 de `CLAUDE.md` («cada ruta declara `response_model`») pasa a ser «cada ruta anota su retorno con un esquema de `app/schemas/`; `response_model` solo cuando difiere del retorno» — T21 la reescribe en `backend/CLAUDE.md`. T5 debe usar `responses=` sin `response_model` redundante.

### Critical Decision — T2: `print` y bind a todas las interfaces
- **What**: `print` → `sys.stderr.write` en `app/core/config.py` y `sys.stdout.write` en `app/scripts/export_openapi.py` (mismo texto y destino); `backend_host = "0.0.0.0"` queda con `# noqa: S104` y un comentario (Docker publica el puerto desde el contenedor).
- **Why**: `T201` y `S104` son nuevas con AC-23; el comportamiento de `python -m app` (mensaje `Configuración inválida: <VARIABLE>`, exit 1) no cambia.
- **Affects**: `app/core/config.py`, `app/scripts/export_openapi.py`. T8 puede reemplazar el `sys.stderr.write` por structlog si lo considera.

### Critical Decision — T2: test extra `tests/test_deps.py`
- **What**: se agregó `tests/test_deps.py` (no listado en Affected files): ejercita `SessionDep`/`get_session` con una ruta de prueba y el `lifespan` de `app/main.py`.
- **Why**: con `--cov-branch` el esqueleto quedaba en 84 % (< `fail_under = 85`); `deps.py`, `get_session` y el `lifespan` no tenían tests. Ahora la cobertura es 99 %.
- **Affects**: ninguno fuera del backend.

### Critical Decision — T1: reglas de Oxlint y overrides (vp 1.7.0 / Oxlint 1.94.0)
- **What**: existen con esos nombres `no-restricted-imports`, `no-restricted-globals`, `no-restricted-properties`, `no-console`, `import/no-cycle`, `react/no-danger`, `react/exhaustive-deps`, `react/only-export-components`, `typescript/no-explicit-any`, `typescript/no-non-null-assertion`, `typescript/no-floating-promises` (type-aware) y `typescript/ban-ts-comment`. Probado con probes temporales: `import/no-cycle` detecta un ciclo escrito con `@/`; un `override` con `"off"` apaga `no-restricted-globals` en `src/api/mutator.ts`; un `override` que redefine `no-restricted-imports` **reemplaza** sus opciones (no las combina). Se agrega `no-restricted-properties` con `window.fetch` y `globalThis.fetch` (ambos detectados), apagado también en el override del mutator.
- **Why**: el bloque `lint` del plan funciona tal cual; el único override previsto no toca `no-restricted-imports`. Si en el futuro un override necesita patrones extra, debe repetir `RESTRICTED_IMPORTS` completo.
- **Affects**: T7 (`frontend/vite.config.ts`): agregar `"no-restricted-properties"` en `rules` y en el override de `mutator.ts`. Con `correctness`/`suspicious` en `error` y los plugins nuevos, el esqueleto dispara además `react/react-in-jsx-scope` (suspicious; se apaga con `"off"` justificado: `jsx: react-jsx`), `import/no-unassigned-import` en `src/test/setup.ts` (override para setup de tests), `vitest/require-mock-type-parameters` en `HomeScreen.test.tsx` (desaparece con la migración a MSW de T10, o se tipa el mock) y `typescript/no-unsafe-type-assertion` en `src/api/mutator.ts:37` (se corrige o se justifica en T7). T14: probe `raw-fetch` puede cubrir también `window.fetch` con `no-restricted-properties`.

### Critical Decision — T1: `vp check --fix` existe; `tsconfig.node.json` no lo type-checkea `vp check`
- **What**: `vp check --fix` existe en vp 1.7.0 (también `--deny-warnings`), así que `frontend_quick` queda como en el plan. `vp check` solo type-checkea `src/` (22 archivos): un error de tipos en `vite.config.ts`/`playwright.config.ts` bajo `tsconfig.node.json` no lo detecta.
- **Why**: sin un chequeo explícito, los flags de AC-32 en `tsconfig.node.json` serían inertes.
- **Affects**: T3 agrega a `frontend/package.json` el script `"typecheck:node": "tsc -p tsconfig.node.json"` y T14 lo suma a `frontend_full` (`vp run typecheck:node`, después de `vp check`). Es el `tsc` del devDependency `typescript` ya existente: sin dependencias nuevas.

### Critical Decision — T1: flags estrictos de TS compatibles con `generated/` y AntD
- **What**: con `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature` y `noImplicitReturns` en `tsconfig.json`, `vp check` y `tsc -p tsconfig.json` (que incluye `src/api/generated/`) pasan sin cambios. En `tsconfig.node.json` aparecen tres errores, todos arreglables sin desactivar flags: `process.env.CI` → `process.env["CI"]` en `playwright.config.ts` (2), `env.BACKEND_URL` → `env["BACKEND_URL"]` en `vite.config.ts`, y `plugins: lazyPlugins(() => [react()])` devuelve `PluginOption[] | undefined`, incompatible con `exactOptionalPropertyTypes` → `lazyPlugins(() => [react()]) ?? []`. Con esos tres cambios `tsc -p tsconfig.node.json` y `vp check` salen con 0.
- **Why**: se mantienen los tres flags en ambos tsconfig, como pide AC-32.
- **Affects**: T7 aplica los tres arreglos en `frontend/vite.config.ts` y `frontend/playwright.config.ts` (este último no figuraba en Affected files: cambia solo el acceso a `CI`).

### Critical Decision — T1: `uv audit` sigue experimental → `pip-audit`
- **What**: `uv audit` existe en uv 0.13.9 pero imprime «`uv audit` is experimental and may change without warning» (uv local es 0.9.0, sin el subcomando). Se mantiene el camino del plan: `uv export --frozen --no-hashes --no-emit-package market-data-client --no-emit-package matriz-client` → `uvx pip-audit@2.10.1 --strict --disable-pip --no-deps -r <archivo> -f json`. Probado: exporta sin las fuentes git y pip-audit sale con 0 («No known vulnerabilities found»).
- **Why**: el NFR pide gates estables; un comando experimental puede cambiar flags o formato JSON sin aviso.
- **Affects**: T18 (`scripts/audit.py`) fija `pip-audit@2.10.1`. Revisar `uv audit` cuando salga de preview.

### Critical Decision — T1: Squawk vía `uvx --from squawk-cli@2.74.0 squawk`, sin `--assume-in-transaction`
- **What**: `uvx squawk-cli@…` no funciona (el paquete expone el binario `squawk`); el comando es `uvx --from squawk-cli@2.74.0 squawk --stdin-filepath alembic-upgrade.sql` leyendo el SQL por stdin. `alembic upgrade --sql` ya emite `BEGIN;`/`COMMIT;` explícitos, y con `--assume-in-transaction` Squawk reporta `transaction-nesting` como falso positivo, así que **no** se usa ese flag. Squawk sale con 1 ante cualquier warning (bloqueante, como pide AC-42). Sobre el SQL del esqueleto, la tabla `alembic_version` (`VARCHAR(32)`) dispara `prefer-text-field`; además todo DDL dispara `require-lock-timeout` y `require-statement-timeout`.
- **Why**: evitar falsos positivos sin debilitar las reglas que importan (`adding-required-field`, locks).
- **Affects**: archivo nuevo `backend/.squawk.toml` (T6) con `pg_version = "17.0"` y `excluded_rules = ["prefer-text-field"]` + comentario (la dispara la tabla interna de Alembic; los tipos de columnas propias los vigila `test_domain_types.py`). T6: `migrations/env.py` emite `SET lock_timeout = '5s'` y `SET statement_timeout = '60s'` antes de las migraciones en modo offline y online. T14: `migrations_full` usa `uv run alembic upgrade head --sql | uvx --from squawk-cli@2.74.0 squawk --stdin-filepath alembic-upgrade.sql` desde `backend/`. Probado: con esa config el SQL de `alembic_version` pasa y un `ADD COLUMN … NOT NULL` sin default falla con `adding-required-field`.

### Critical Decision — T1: transporte ASGI de Schemathesis 4
- **What**: con `schemathesis==4.34.1`, `schemathesis.openapi.from_path(path)` (sin parámetro `app`) y `case.call_and_validate(app=create_app())` usan el transporte ASGI en proceso, sin servidor y sin warnings (probado con `-W error`). Asignar `schema.app = app` después de `from_path` **no** funciona (`TypeError: 'NoneType' object is not callable`).
- **Why**: es la firma exacta que el plan dejaba abierta.
- **Affects**: el `uv.lock` de T2 ya resuelve `schemathesis` 4.34.1, la versión probada. T9 usa `case.call_and_validate(app=APP)` con `APP = create_app()` a nivel de módulo (una instancia por sesión de tests).

### Critical Decision — T1: Renovate extrae `[tool.uv.sources]` sin `customManagers`
- **What**: Renovate 44.259.0 (`--platform=local --dry-run=extract`, requiere Node ≥ 24) detecta con el manager `pep621` las dos fuentes git como `depType: tool.uv.sources`, `datasource: github-tags`, `packageName: gravity-quant/market-libs` y `currentValue: <paquete>-vX.Y.Z`. Localmente quedan con `skipReason: github-token-required`, que desaparece con la app de Renovate instalada con acceso a `market-libs`. No hace falta `customManagers`.
- **Why**: como ambos paquetes comparten repo y datasource, el `versioning` regex del plan con grupo `compatibility` (`^(?<compatibility>.+)-v…`) es lo que evita proponer un tag de `matriz-client` para `market-data-client`; se mantiene.
- **Affects**: T19 usa el `renovate.json` del plan sin `customManagers`. Queda para verificar en el primer PR de Renovate que el `uv lock` del artefacto pueda clonar `ssh://git@github.com/…` (lo resuelve la reescritura de host rules de Renovate; si no, se agrega `hostRules` en T19). T21 documenta en el README que `renovate-config-validator` requiere Node ≥ 24.

### Critical Decision — T3: dependency-cruiser parsea con swc (`@swc/core` como devDependency nueva)
- **What**: `.dependency-cruiser.cjs` usa `options.parser: "swc"` y se agrega `@swc/core` a devDependencies. Su postinstall se deniega en `frontend/pnpm-workspace.yaml` (`allowBuilds`), porque el binario nativo llega por `optionalDependencies`.
- **Why**: dependency-cruiser 18.9 no soporta TypeScript 7.0 (`missing-typescript-transpiler`: «typescript@7.0 is not supported as its API lacks what dependency-cruiser needs») y sin transpiler analizaba 0 módulos con exit 0, o sea que pasaba sin verificar nada. Con swc analiza los 27 módulos y resuelve `@/` vía `tsconfig.json`. Probes temporales confirmaron que disparan `no-circular`, `screen-no-otra-screen`, `components-limites`, `utils-constants-puros` y `screen-via-index`, con origen → destino en `--output-type err`.
- **Affects**: `frontend/package.json`, `frontend/pnpm-workspace.yaml`, `frontend/knip.config.ts` (`@swc/core` en `ignoreDependencies`) y la lista de dependencias justificadas que documenta T21.

### Critical Decision — T3: versiones fijadas de `msw` y `@vitest/coverage-v8`
- **What**: `msw` queda en `^2.15.0`, no en `latest` (3.0.7), y `@vitest/coverage-v8` en `5.1.0` exacto. El postinstall de `msw` se deniega en `allowBuilds`.
- **Why**: Resolved Decisions fija MSW 2, y su postinstall solo copia `mockServiceWorker.js` para el navegador, mientras que los tests usan `setupServer` de Node. `@vitest/coverage-v8@5.1.1` exige `vitest@5.1.1` como peer y metía un segundo Vitest en el lockfile, distinto del 5.1.0 que trae `vp` 1.7.0. Renovate debe subir ese paquete junto con `vite-plus`.
- **Affects**: T7 (provider de cobertura), T10 (MSW) y T19 (conviene agrupar `@vitest/coverage-v8` con `vite-plus` en `renovate.json`).

### Critical Decision — T3: `ignoreDependencies` transitorios en `knip.config.ts`
- **What**: además de `@faker-js/faker`, quedan ignoradas, con comentario cada una: `@vitest/coverage-v8` (Vitest la carga dinámicamente), `@swc/core` (la carga dependency-cruiser), `zustand` (es del stack pero todavía no hay ningún store), `msw` (se quita en T10) y `@axe-core/playwright` (se quita en T12). Las entradas `src/main.tsx` y `src/test/setup.ts` se quitaron de `entry` porque knip las marcaba como redundantes: ya las detectan sus plugins.
- **Why**: AC-31 exige exit 0 sobre el esqueleto, y esas dependencias se instalan en T3 pero se usan en tareas posteriores. Probé que un export sin uso agregado a mano sigue haciendo fallar `lint:unused`.
- **Affects**: T10 y T12 deben quitar `msw` y `@axe-core/playwright` de `ignoreDependencies`. El primer store de Zustand debe quitar `zustand`.

### Critical Decision — T3: límite provisional de `size-limit`
- **What**: el bloque `size-limit` queda con `"limit": "300 kB"` como valor provisional.
- **Why**: el plan asigna la medición a T14 (medición + 10 %, redondeado al múltiplo de 5 kB siguiente), pero el bloque tenía que existir y ser válido desde T3.
- **Affects**: T14 reemplaza el valor por el medido.

### Critical Decision — T5: Headers de `HTTPException` y status sin frase estándar
- **What**: el handler de `HTTPException` reenvía `exc.headers` (p. ej. `Allow` en un 405) y, si `HTTPStatus(status)` no existe (p. ej. 599), usa `title = "Error"`. `test_errors.py` monta sus endpoints de prueba con `ASGITransport(raise_app_exceptions=False)`, porque `ServerErrorMiddleware` re-lanza la excepción después de responder el 500.
- **Why**: la tabla de mapeo no lo cubría; perder `Allow`/`WWW-Authenticate` rompería la semántica HTTP y `HTTPStatus(599)` lanzaría `ValueError` dentro del handler.
- **Affects**: `backend/app/api/errors.py`, `backend/tests/test_errors.py`. `backend/openapi.json` ya declara `ProblemDetails`; el cliente Orval se regenera en T10.

### Critical Decision — T7: test extra `src/app/providers.test.tsx` para el umbral de branches
- **What**: se agregó `frontend/src/app/providers.test.tsx` (no listado en Affected files): renderiza `AppProviders` sin `queryClient` y verifica que el `QueryClient` por defecto usa los defaults de `createQueryClient` (`staleTime: 30000`). Usa `render` directo, no `renderWithProviders`, porque prueba justamente el camino sin cliente inyectado.
- **Why**: con los umbrales de AC-36 el esqueleto quedaba en 68,75 % de branches (< 70 %); la rama `queryClient ?? defaultClient` no tenía test. Ahora: líneas 91,66 %, branches 75 %.
- **Affects**: ninguna otra tarea. T13 seguirá subiendo la cobertura de `mutator.ts` (ramas de `parseBody`).

### Critical Decision — T7: `coverage/**` en `fmt.ignorePatterns` y `as T` justificado en el mutator
- **What**: `fmt.ignorePatterns` de `vite.config.ts` suma `coverage/**` (además de `lint.ignorePatterns`). El `as T` de `customFetch` (`src/api/mutator.ts`) queda con `oxlint-disable-next-line typescript/no-unsafe-type-assertion` y un comentario: es el contrato del mutator de Orval. `HomeScreen.test.tsx` tipa el `vi.fn` señalado por `vitest/require-mock-type-parameters` (T10 lo reemplaza por MSW).
- **Why**: tras `vp test run --coverage`, Oxfmt revisaba los HTML del reporte y `vp check` fallaba con 20 archivos «mal formateados». El `as T` no se puede evitar sin validar en runtime cada respuesta.
- **Affects**: `frontend/vite.config.ts`, `frontend/src/api/mutator.ts` (T13 debe conservar el comentario), `frontend/src/screens/HomeScreen/HomeScreen.test.tsx`. Nota de entorno: con `NODE_ENV=production` exportado en la shell (como en esta máquina) `vp test` falla con `React.act is not a function`; T14 debería hacer `unset NODE_ENV` en `frontend_full` de `scripts/gate.sh`.

### Critical Decision — T6: `testcontainers.community.postgres` y socket de Ryuk
- **What**: `tests/test_migrations.py` importa `PostgresContainer` de `testcontainers.community.postgres` (no de `testcontainers.postgres`), y el fixture define `TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock` solo durante el test y solo si el entorno no lo trae ya.
- **Why**: con testcontainers 4.x `testcontainers.postgres` emite un `DeprecationWarning`, que `filterwarnings = ["error"]` convierte en error de colección. En Docker Desktop para macOS el socket detectado (`~/.docker/run/docker.sock`) no se puede montar en el contenedor Ryuk (`mkdir ... operation not supported`); `/var/run/docker.sock` funciona ahí y es el socket estándar del runner Linux de CI.
- **Affects**: `backend/tests/test_migrations.py`. Ningún prerrequisito extra para T14/T17 ni para el README (T21).

### Critical Decision — T6: detalles de `env.py`, `alembic.ini` y la plantilla
- **What**: `env.py` crea el engine con `create_async_engine(database_url(), poolclass=NullPool)` en vez de `async_engine_from_config` (la URL de `Settings` no pasa por `configparser`, que interpreta `%`); usa `compare_type=True`; llama a `fileConfig(..., disable_existing_loggers=False)` para no silenciar los loggers del proceso que invoca a Alembic (relevante para T8). `alembic.ini` usa `prepend_sys_path = %(here)s` y `timezone = UTC`. `script.py.mako` se modernizó (`str | Sequence[str] | None`, imports ordenados, docstrings en español) para que las migraciones generadas pasen Ruff (`UP`, `I`) y mypy. Se borró el `migrations/README` que genera `alembic init`.
- **Why**: que la config funcione igual desde el CLI, los tests y el gate `migrations` sin tocar el logging de la app.
- **Affects**: `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`. `backend/.squawk.toml` se creó como lo pedía la decisión de T1 (verificado: `alembic upgrade head --sql | squawk` sale con 0).

### Critical Decision — T8: `correlation_id` por procesador en vez de `bind_contextvars` en el middleware
- **What**: `app/core/logging.py` agrega el procesador `add_correlation_id`, que lee el `ContextVar` de `asgi_correlation_id` en cada evento (structlog y stdlib). `AccessLogMiddleware` no hace `bind_contextvars`/`clear_contextvars`: es un middleware ASGI puro que solo emite el evento `request`. `merge_contextvars` sigue en la cadena para binds futuros. Además se agregó `ExtraAdder`, `add_logger_name` y `dict_tracebacks` (solo en JSON).
- **Why**: el log del handler de `Exception` (T5) corre en `ServerErrorMiddleware`, por fuera de los middlewares; con bind/clear ese log perdía el `correlation_id`. El `ContextVar` de `asgi_correlation_id` sigue visible ahí.
- **Affects**: `backend/app/core/logging.py`, `backend/app/api/middleware.py`.

### Critical Decision — T8: fixture `restore_logging` en `conftest.py` y ajuste de `test_errors.py`
- **What**: `tests/conftest.py` suma un fixture autouse que restaura los handlers y el nivel del root logger y llama `structlog.reset_defaults()` después de cada test. En `tests/test_errors.py`, `test_unhandled_exception_echoes_correlation_id` deja de fijar el `ContextVar` a mano y manda un `X-Request-ID` válido por header.
- **Why**: el `lifespan` (ejercido por `test_deps.py`) ahora llama `configure_logging`, que reemplaza los handlers del root; sin restaurarlo, el estado se filtraba entre tests en orden aleatorio. Con `CorrelationIdMiddleware` montado, el valor fijado a mano se pisaba con uno generado.
- **Affects**: `backend/tests/conftest.py`, `backend/tests/test_errors.py` (archivos fuera de Affected files de T8).

### Critical Decision — T11: type guard en lugar de `as Intl.StringNumericLiteral`
- **What**: `src/utils/format.ts` no usa `value as Intl.StringNumericLiteral`. Un guard `isNumericLiteral` (`Number(value)` solo para validar) acota el string, que se le pasa intacto a Intl. Un string no numérico se formatea como `Number.NaN` y da `"NaN"`, el mismo resultado que preveía el plan.
- **Why**: la regla `typescript/no-unsafe-type-assertion` (categoría `suspicious` en `error`, T7) rechaza el `as` aunque esté justificado con un comentario.
- **Affects**: `frontend/src/utils/format.ts`, `frontend/src/utils/format.test.ts` (se agrega un caso para el string no numérico).

### Critical Decision — T12: contraste corregido en `src/app/theme.ts`, no en las pantallas
- **What**: las únicas violaciones de axe fueron `color-contrast` (WCAG 1.4.3) en Home y 404: el subtítulo de `Result` (`colorTextDescription`, 3.29:1) y el link «Volver al inicio» (`#1677ff`, 3.76:1) sobre el fondo `#f5f5f5` del Layout. Se corrigieron con tokens en `src/app/theme.ts` (`colorPrimary` y `colorLink` = `#0958d9`, blue-7 de AntD, 5.6:1; `colorTextDescription` = `rgba(0, 0, 0, 0.65)`, 6.7:1), sin tocar `src/screens/` ni `src/layouts/`. `a11y.spec.ts` compara un resumen (`id`, `impact`, `target`, `failureSummary`) contra `[]` para que la falla sea legible.
- **Why**: el problema está en los tokens por defecto de AntD, no en el markup, y CLAUDE.md §7 exige configurar colores solo en `theme.ts` vía `ConfigProvider`. Un fondo blanco en el Layout no alcanzaba (los mismos colores dan 3.4:1 y 4.1:1 sobre `#fff`).
- **Affects**: `frontend/src/app/theme.ts` (archivo fuera de la lista de T12), `frontend/e2e/a11y.spec.ts`. Cualquier pantalla nueva hereda el primario más oscuro.

### Critical Decision — T13: `isProblemDetails` queda privado y exige `title` string y `status` number
- **What**: el guard no se exporta desde `src/api/mutator.ts` (el plan lo mostraba exportado) y, además de la presencia de `title` y `status`, verifica sus tipos.
- **Why**: nadie fuera del mutator lo usa, y un export sin consumidores hace fallar `vp run lint:unused` (knip, AC-31). Chequear tipos evita tomar como `ProblemDetails` un JSON arbitrario con esas claves.
- **Affects**: `frontend/src/api/mutator.ts`. Si una pantalla necesita discriminar errores, se exporta junto con su primer uso.

### Critical Decision — T14: probes como árboles que replican el módulo, con rutas explícitas
- **What**: cada probe es un directorio `scripts/guard-probes/<módulo>/<probe>/` que replica la raíz del módulo (p. ej. `backend/utcnow/app/_probe.py`, `frontend/cycle/src/utils/_probeA.ts` + `_probeB.ts`), no un archivo suelto como `backend/utcnow.py`. `verify-guards.sh` lo copia con `cp -R`, borra todo `_probe*` de `app/` o `src/` después de cada probe y en el `trap`, y a las herramientas por archivo (`ruff check`, `vp lint`, `vp check`) les pasa las rutas del probe de forma explícita. El probe `enum` usa `vp check <archivo>` y `raw-fetch` cubre también `window.fetch` (`no-restricted-properties`). `lint-imports` corre con `--no-cache`. `.gitignore` agrega `**/_probe*` con la excepción `!scripts/guard-probes/**`, para que las fuentes de los probes se versionen.
- **Why**: los probes de varios archivos (ciclo, hook → componente) necesitan un destino por archivo, y un árbol espejo lo resuelve sin manifiesto. `vp check` sin argumentos respeta `.gitignore` y no veía el `enum` (salía con 0); con la ruta explícita falla con TS1294.
- **Affects**: `scripts/verify-guards.sh`, `scripts/guard-probes/**`, `.gitignore`. Un probe nuevo es un directorio más y una línea `run_probe` en `verify-guards.sh`.

### Critical Decision — T14: `utils-constants-puros` no detectaba imports con `@/`
- **What**: en `frontend/.dependency-cruiser.cjs`, la regla `utils-constants-puros` deja de filtrar por `dependencyTypes` (`to: { pathNot: "^src/(types|utils|constants)/" }`) y excluye del origen los `*.test.ts(x)` (`from.pathNot`).
- **Why**: el probe `utils-to-api` pasaba sin errores. Con el parser swc (decisión de T3), un import `@/api/...` queda con `dependencyTypes: ["undetermined", "import"]`, que el filtro `["local", "aliased", "npm", "npm-dev"]` no incluía. Sin el filtro, la regla quedó demasiado amplia: marcaba `src/utils/format.test.ts → vite-plus/test`. Los tests no son código de la capa, por eso se excluyen del origen.
- **Affects**: `frontend/.dependency-cruiser.cjs` (archivo de T3). Los paquetes npm siguen prohibidos en `utils/` y `constants/` porque su ruta resuelta está en `node_modules/`.

### Critical Decision — T14: entorno de `gate.sh` y `typecheck:node`
- **What**: `scripts/gate.sh` hace `unset NODE_ENV`, antepone `frontend/node_modules/.bin` al `PATH` para usar el `vp` del devDependency `vite-plus` sin instalador global, exporta `LC_ALL` y verifica con `need` que existan `uv`, `vp` y `docker` (este último solo en `migrations`); si falta alguno, sale con 1 y nombra la herramienta. Es compatible con el bash 3.2 de macOS (sin `mapfile` y con `${var}` delante de caracteres no ASCII). `frontend_full` corre `vp run typecheck:node` después de `vp check`. El script `"typecheck:node": "tsc -p tsconfig.node.json"` se agregó en este paso a `frontend/package.json`, porque T3 no lo había creado. `migrations_full` usa `uvx --from squawk-cli@2.74.0 squawk --stdin-filepath alembic-upgrade.sql` (decisión de T1). `file` sin ruta y `e2e`/`migrations` en modo `quick` salen con 64.
- **Why**: en esta máquina, `NODE_ENV=production` está exportado y `vp` no está en el `PATH` global. Sin estos ajustes, el gate falla por causas de entorno y no del código.
- **Affects**: `scripts/gate.sh`, `frontend/package.json`. T15 a T17 invocan el script sin preparar el entorno. T17 puede omitir el `echo … >> $GITHUB_PATH` que preveía el plan.

### Critical Decision — T14: presupuesto de bundle en 240 kB
- **What**: `vp build && vp run size` midió 214,99 kB gzip en `dist/assets/*.js`. Con 10 % más (236,49 kB) y el redondeo hacia arriba al siguiente múltiplo de 5 kB, el `limit` queda en `"240 kB"` (antes, `300 kB` provisional).
- **Why**: es la regla de AC-39 del plan.
- **Affects**: `frontend/package.json`. Para subir el límite hay que justificarlo en el PR.

### Critical Decision — T15: `glob` de lefthook como lista con el nivel raíz del módulo
- **What**: en `lefthook.yml` se usa `glob: ["backend/*.py", "backend/**/*.py"]` y `glob: ["frontend/*.{ts,tsx}", "frontend/**/*.{ts,tsx}"]`, en vez del `"backend/**/*.py"` y `"frontend/**/*.{ts,tsx}"` del plan.
- **Why**: en lefthook 2.2.2, `**/` exige al menos un directorio intermedio. Con el glob del plan, un commit de `backend/b.py` mostraba `backend (skip) no matching staged files`, y quedaban sin gate `frontend/vite.config.ts`, `playwright.config.ts`, `orval.config.ts` y `knip.config.ts`.
- **Affects**: `lefthook.yml` (AC-9, AC-10).

### Critical Decision — T16: hooks de `.claude/` cerrados ante fallas y `.env*` en cualquier carpeta
- **What**: si falta `jq`, los tres hooks salen con `exit 2` y nombran la herramienta, así que `guard-paths.sh` bloquea la edición en lugar de dejarla pasar. `guard-paths.sh` compara el nombre del archivo (`.env` y `.env.*`, salvo `.env.example`) en cualquier carpeta, no solo en la raíz. Las rutas fuera del repo no se controlan. `fmt-lint-file.sh` solo llama a `scripts/gate.sh file` para `backend/*.py` y `frontend/*.ts(x)` que existen. `.octo/hooks/code-validate-improve.json` ya usaba `scripts/gate.sh branch full` y no mencionaba `npm`, así que no se modificó.
- **Why**: el plan pide que ningún gate se saltee en silencio. CLAUDE.md prohíbe `backend/.env` y `frontend/.env`, por lo que bloquearlos también es coherente.
- **Affects**: `.claude/hooks/{guard-paths,fmt-lint-file,stop-gate}.sh`. Para probar el hook Stop a mano no sirven archivos `_probe*`: están en `.gitignore` y Ruff y `vp` los ignoran.

### Critical Decision — T18: `audit.py` se re-ejecuta con uv si Python < 3.11, y valida la allowlist
- **What**: `tomllib` necesita Python 3.11+, pero el `python3` de macOS puede ser más viejo (localmente es 3.9). En ese caso el script se re-ejecuta con `uv run --no-project --python '>=3.11'`. También acepta `--allowlist RUTA` (para probar sin tocar el archivo versionado). Una entrada a la que le falta `id`, `ecosystem`, `package`, `reason` o `expires`, que tiene un `ecosystem` distinto de `PyPI`/`npm` o un `expires` que no es fecha TOML hace fallar igual que una vencida. Una entrada aplica si el `id` coincide con el id del hallazgo o con alguno de sus alias, y los nombres de PyPI se comparan normalizados (PEP 503). Si pip-audit saltea un paquete (`skip_reason`), falla. OSV-Scanner fijado localmente en 2.7.1 (`brew install osv-scanner`).
- **Why**: el outcome se verifica con `python3 scripts/audit.py`, y no hacía falta otra dependencia. Sin validación de la allowlist, una entrada mal escrita sin `expires` nunca vencería.
- **Affects**: `scripts/audit.py`, `security-allowlist.toml`. T17 (job `security`) necesita `uv` y `osv-scanner` en el PATH. T21 documenta `brew install osv-scanner` en el README.

### Critical Decision — T17: versiones fijadas, binarios verificados y zizmor con auditorías online
- **What**: acciones fijadas por SHA (checkout v7.0.1, setup-uv v10.4.0, pnpm/action-setup v6.1.1, setup-node v7.1.0, upload-artifact v7.0.2, paths-filter v4.0.3). actionlint 1.7.12, gitleaks 8.30.1 y OSV-Scanner 2.7.1 se bajan de sus releases y se verifican con `sha256sum -c`; zizmor 1.33.1 corre vía `uvx` con `GH_TOKEN: github.token` (sin `--offline`) para que también corran `impostor-commit` y `known-vulnerable-actions`. El job `security` instala `osv-scanner` en el `PATH` antes de `python3 scripts/audit.py` (T18 lo invoca por nombre). Node 22 (el de desarrollo) y la versión de pnpm sale de `packageManager` vía `package_json_file`. En `push`, si `github.event.before` es el SHA nulo (rama nueva), gitleaks recorre todo el historial. Cada job tiene `timeout-minutes`.
- **Why**: el plan dejaba `<sha>`/`<versión>` abiertos y no decía de dónde salía `osv-scanner` en CI. Localmente `actionlint` y `zizmor --persona pedantic` salen sin hallazgos.
- **Affects**: `.github/workflows/ci.yml`; T18 (`scripts/audit.py` asume `osv-scanner` en el `PATH`); Renovate (T19) actualiza los SHA de las acciones, pero las variables `*_VERSION`/`*_SHA256` del bloque `env` se suben a mano. El «primer PR con `ci-ok` en verde» queda para T22: requiere el secret `MARKET_LIBS_TOKEN` y `scripts/audit.py` (T18).

### Critical Decision — T19: grupo `vite-plus` en `renovate.json`
- **What**: además de lo que define el plan, se agrega una `packageRule` que agrupa `vite-plus` y `@vitest/coverage-v8` en el grupo `vite-plus`. Va después de la regla `frontend/**` para que prevalezca su `groupName`. No se agregaron `customManagers` ni `hostRules` (T1).
- **Why**: la Critical Decision de T3 fija `@vitest/coverage-v8` al Vitest que trae `vite-plus`; si se suben por separado, el lockfile vuelve a tener dos Vitest. `renovate-config-validator` (también con `--strict`) sale con 0. Con Node 22, `npx` resuelve renovate 42.x; el validador de la versión actual pide Node ≥ 24.
- **Affects**: `renovate.json`; T21 (README: el grupo `vite-plus` y el requisito de Node para el validador).

### Critical Decision — T21: referencias a la numeración vieja de `CLAUDE.md` actualizadas fuera de la lista de T21
- **What**: con el `CLAUDE.md` raíz reducido a seis secciones (la checklist pasa a ser §6 y la Definición de terminado §5), se actualizaron las referencias que apuntaban a la numeración vieja: el encabezado y la checklist de `.github/pull_request_template.md` (copia literal de la nueva §6), el mensaje de `scripts/hooks/check-generated-sync.sh` (ahora remite a `frontend/CLAUDE.md`, «Flujo para cambiar el contrato», como preveía el plan) y comentarios de `frontend/.dependency-cruiser.cjs`, `frontend/knip.config.ts` y `frontend/vite.config.ts`. La checklist reemplaza `response_model` por «esquema de respuesta (anotación de retorno)» (decisión de T2, `FAST001`) y suma un ítem de `Decimal`/`string` y fechas con zona horaria.
- **Why**: AC-61 pide que la plantilla copie la checklist de `CLAUDE.md`, y el NFR «Documentación coherente» no admite referencias a secciones que ya no existen.
- **Affects**: `.github/pull_request_template.md`, `scripts/hooks/check-generated-sync.sh`, `frontend/.dependency-cruiser.cjs`, `frontend/knip.config.ts`, `frontend/vite.config.ts` (solo comentarios y texto; `vp run lint:arch` y `scripts/gate.sh file` en verde).

### Critical Decision — T21: bullets del steering con resumen en la misma línea
- **What**: en `.octo/steering/*.md`, los bullets con sub-lista (`**Target users**`, `**Key directories**`, etc.) llevan un resumen corto después de los dos puntos.
- **Why**: el chequeo de AC-58 en Verification (`grep -nE "^- \*\*.*\*\*: *$"`) trata un bullet que termina en `:` como placeholder vacío, aunque tenga sub-bullets debajo.
- **Affects**: `.octo/steering/{product,tech,structure}.md`.

### Critical Decision — T22: verificación en clon limpio; CI y escenarios de GitHub quedan pendientes
- **What**: el «clon limpio» es una copia en `/tmp` de los archivos versionados y no ignorados del working tree (`git ls-files -co --exclude-standard`), porque todo el spec sigue sin commitear en `main`. Con `.env` copiado de `.env.example`, `uv sync --frozen` y `pnpm install --frozen-lockfile`: `scripts/gate.sh backend full` (0, 28 s, cobertura 99,66 %, 6 probes), `frontend full` (0, 18 s, 10 probes, bundle 215 kB de 240 kB), `e2e` (0, 4 s, 4 tests con axe) y `migrations` (0, 7 s, Squawk sin hallazgos). lefthook 2.2.2 y gitleaks 8.30.1 se instalaron en directorios temporales (equivalente a `brew install`). Medido: `pre-commit` con 10 archivos en un módulo, 1,4 s (backend) y 1,6 s (frontend) con caché, 5,4 s con caché fría (NFR < 20 s); `PostToolUse`, 0,4 s (`.py`) y 0,8 s (`.tsx`) (NFR < 10 s). AC-8 a AC-19, AC-43, AC-44 (actionlint y zizmor locales), AC-45, AC-58, AC-59 (97 líneas) y AC-60 se comportan como pide Verification.
- **Why**: el NFR de CI (`ci-ok` < 10 min) y los escenarios de AC-1 a AC-7 que dependen de GitHub (filtro por rutas, caché, secret ausente, ruleset aplicado, plantilla de PR) requieren commitear, pushear una rama y abrir un PR, y además el secret `MARKET_LIBS_TOKEN` todavía no existe en el repo (`gh secret list` vacío). Son acciones externas que decide el mantenedor; no se ejecutaron en T22.
- **Affects**: AC-1 a AC-7 y el NFR de velocidad de CI quedan para el primer PR de esta rama (crear el secret, abrir el PR y aplicar `.github/rulesets/main.json`). Hallazgo de entorno, no del repo: el shim de corepack de esta máquina busca `pnpm.cjs` y pnpm 12.23.0 trae `pnpm.mjs`, así que `pnpm` falla con `MODULE_NOT_FOUND`; se instaló con `node <caché de corepack>/pnpm/12.23.0/bin/pnpm.mjs install --frozen-lockfile`. El `vp build` emite el aviso de Vite «chunk > 500 kB» (no corta el gate; el presupuesto lo controla size-limit).
