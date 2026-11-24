# Guardas de calidad y buenas prácticas

Segunda etapa de `matriz-trader`: convierte las convenciones del proyecto en gates bloqueantes antes de empezar con las funcionalidades. La mayor parte del código la escriben agentes de IA, que cumplen lo que se verifica de forma automática pero no siempre lo que solo está escrito. Los comandos están en [`CLAUDE.md`](../CLAUDE.md) y la instalación de las herramientas, en [`README.md`](../README.md). Este documento resume qué se construyó y por qué.

## Un solo script, cuatro momentos

`scripts/gate.sh <módulo> <quick|full>` es el único lugar donde se define qué corre cada gate. Los demás solo lo invocan:

| Momento | Consumidor | Gate |
|---|---|---|
| El agente edita un archivo | `.claude/hooks/fmt-lint-file.sh` (`PostToolUse`) | `file <ruta>` |
| El agente intenta terminar el turno | `.claude/hooks/stop-gate.sh` (`Stop`) | `changed full` |
| Se completa una wave de Octo | `.octo/hooks/code-validate-improve.json` | `branch full` |
| `git commit` | `lefthook.yml` | `<módulo> quick` |
| PR contra `main` | `.github/workflows/ci.yml` | `full`, `e2e`, `migrations` |

`scripts/verify-guards.sh` inyecta violaciones de prueba (`scripts/guard-probes/`) y exige que cada herramienta las rechace. Si un gate deja de detectar algo, también falla.

## Qué incluye

| Parte | Contenido |
|---|---|
| Backend | Capas con import-linter, Ruff ampliado (async, seguridad, fechas, FastAPI), errores RFC 9457 con `correlation_id`, logging con structlog, `Clock` en UTC, tipos `Price`/`Quantity`/`Money` sobre `Decimal` y Alembic async. Tests: cobertura ≥ 85 %, Hypothesis, Schemathesis y testcontainers. |
| Frontend | Oxlint estricto, flags de TypeScript adicionales, dependency-cruiser (`lint:arch`), knip (`lint:unused`), cobertura ≥ 70 %, MSW 2, axe en Playwright, size-limit (240 kB), `ApiError` en el mutator y formatters `es-AR`. |
| Repo | lefthook, gitleaks, `scripts/audit.py` (pip-audit + OSV-Scanner con allowlist que vence), actionlint, zizmor, Renovate, ruleset de `main` y plantilla de PR. |
| Agentes | Hooks de Claude Code que bloquean archivos generados y protegidos, el hook de Octo corregido y el steering completo. `CLAUDE.md` dividido en raíz, `backend/` y `frontend/`. |

## Decisiones principales

- **`quick` en el commit, `full` en el agente y en CI**: un `pre-commit` de varios minutos lleva a usar `--no-verify`. Medido: el `pre-commit` tarda menos de 2 s con caché y el `PostToolUse`, menos de 1 s por archivo.
- **Reglas de carpetas en dependency-cruiser, no en Oxlint**: Oxlint compara el texto del import, no la ruta resuelta, y no puede expresar «una pantalla no importa de otra».
- **`pip-audit` en lugar de `uv audit`**: `uv audit` sigue siendo experimental.
- **Hooks cerrados ante fallas**: si falta `jq`, `uv`, `vp` o Docker, el hook o el gate falla y nombra la herramienta. Ningún gate se saltea en silencio.
- **Contraste corregido en el tema**: las violaciones de axe venían de los tokens por defecto de Ant Design, así que se corrigieron en `src/app/theme.ts` y no en las pantallas.
- **Reglas de órdenes documentadas, no implementadas**: `client_order_id` único, controles de riesgo, kill switch, auditoría de solo inserción y rate limiting quedan como reglas obligatorias en `backend/CLAUDE.md` §8. Se implementan con la primera feature de órdenes.
- **Alembic configurado ahora**: reemplaza la decisión «Sin Alembic por ahora» de la [etapa anterior](quiero-crear-las-bases-para-un-proyecto-de.md), para que `alembic check` y Squawk estén activos desde el primer modelo.

## Pendiente

- Para el primer PR hay que crear el secret `MARKET_LIBS_TOKEN` y aplicar `.github/rulesets/main.json` (el comando `gh api` está en el README). Recién entonces se pueden verificar los escenarios que dependen de GitHub: filtro por rutas, caché, secret ausente y `ci-ok` en menos de 10 minutos.
- Las variables `*_VERSION` y `*_SHA256` de los binarios del CI (actionlint, gitleaks y OSV-Scanner) se actualizan a mano. Renovate solo actualiza los SHA de las acciones.
