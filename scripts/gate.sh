#!/usr/bin/env bash
# Único punto de entrada de los gates de calidad (AC-19). Lo invocan CI, lefthook, el hook Stop de
# Claude Code, el hook de Octo y la ejecución manual; ningún otro archivo repite estos comandos.
#
# Uso: scripts/gate.sh <backend|frontend> [quick|full]       (default: full)
#      scripts/gate.sh <e2e|migrations> [full]
#      scripts/gate.sh <changed|branch> [quick|full]         (módulos con cambios)
#      scripts/gate.sh file <ruta-relativa-a-la-raíz>        (hook PostToolUse)
#
# Salida: 0 si todo pasa, 1 si falla algún comando (su salida queda sin filtrar), 64 si los
# argumentos son inválidos. Compatible con el bash 3.2 de macOS.
set -euo pipefail
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
# Vitest respeta NODE_ENV: con `production` carga el build de producción de React y los tests fallan
# con `React.act is not a function`.
unset NODE_ENV

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# `vp` es el bin del devDependency local `vite-plus`: no hace falta un instalador global.
export PATH="$ROOT/frontend/node_modules/.bin:$PATH"

usage() {
  echo "Uso: scripts/gate.sh <backend|frontend> [quick|full] | <e2e|migrations> [full] | <changed|branch> [quick|full] | file <ruta>" >&2
  exit 64
}
target="${1:-}"
[[ -n "$target" ]] || usage
mode="${2:-full}"

need() { # need <comando> <cómo instalarlo>: ningún gate se saltea en silencio por falta de una herramienta
  command -v "$1" >/dev/null 2>&1 || { echo "Falta '$1': $2" >&2; exit 1; }
}
need_backend() { need uv "instalalo con 'brew install uv' (ver README)"; }
need_frontend() { need vp "corré 'pnpm install' en frontend/ (vp viene del devDependency vite-plus)"; }

backend_quick() {
  need_backend
  cd "$ROOT/backend"
  uv run ruff format . && uv run ruff check --fix . && uv run mypy . && uv run lint-imports
}
backend_full() {
  need_backend
  cd "$ROOT/backend"
  uv run ruff check . && uv run ruff format --check . && uv run mypy . \
    && uv run lint-imports && uv run pytest && "$ROOT/scripts/verify-guards.sh" backend
}
frontend_quick() {
  need_frontend
  cd "$ROOT/frontend"
  vp check --fix && vp run lint:arch
}
frontend_full() {
  need_frontend
  cd "$ROOT/frontend"
  # `typecheck:node`: `vp check` solo type-checkea src/, no vite.config.ts ni playwright.config.ts.
  vp check && vp run typecheck:node && vp run lint:arch && vp run lint:unused \
    && vp test run --coverage && vp build && vp run size && "$ROOT/scripts/verify-guards.sh" frontend
}
e2e_full() {
  need_frontend
  cd "$ROOT/frontend"
  vp run e2e
}
# PostgreSQL 17 lo levanta testcontainers (requiere Docker). `upgrade --sql` es offline: no conecta a
# ninguna DB, pero env.py necesita una DATABASE_URL sintácticamente válida (en CI se exporta una ficticia).
# Squawk lee su config de backend/.squawk.toml.
migrations_full() {
  need_backend
  need docker "instalá Docker Desktop (testcontainers levanta PostgreSQL 17)"
  cd "$ROOT/backend"
  uv run pytest -m db --no-cov \
    && uv run alembic upgrade head --sql \
      | uvx --from squawk-cli@2.74.0 squawk --stdin-filepath alembic-upgrade.sql
}
file_check() { # formatea y lintea UN archivo; lo usa .claude/hooks/fmt-lint-file.sh (AC-15)
  local f="$1"
  case "$f" in
    backend/*.py)
      need_backend
      cd "$ROOT/backend" && uv run ruff format "${f#backend/}" && uv run ruff check --fix "${f#backend/}" ;;
    frontend/src/api/generated/*) return 0 ;;
    frontend/*.ts | frontend/*.tsx)
      need_frontend
      cd "$ROOT/frontend" && vp fmt "${f#frontend/}" && vp lint "${f#frontend/}" ;;
    *) return 0 ;;
  esac
}
run_modules() { # $1 = archivos cambiados; corre el gate de cada módulo tocado y acumula las fallas
  local rc=0
  if grep -q '^backend/' <<<"$1"; then "$0" backend "$mode" || rc=1; fi
  if grep -q '^frontend/' <<<"$1"; then "$0" frontend "$mode" || rc=1; fi
  return "$rc"
}
untracked() { git -C "$ROOT" ls-files --others --exclude-standard; }
changed() { # cambios sin commitear (tracked + untracked) respecto de HEAD — hook Stop (AC-16)
  run_modules "$({ git -C "$ROOT" diff --name-only HEAD; untracked; } | sort -u)"
}
branch() { # todo lo que la rama cambió respecto de origin/main, commiteado o no — hook de Octo (AC-18)
  local base
  base="$(git -C "$ROOT" merge-base HEAD origin/main 2>/dev/null || git -C "$ROOT" rev-parse HEAD)"
  run_modules "$({ git -C "$ROOT" diff --name-only "$base"; untracked; } | sort -u)"
}

case "$target:$mode" in
  backend:quick) backend_quick ;;
  backend:full) backend_full ;;
  frontend:quick) frontend_quick ;;
  frontend:full) frontend_full ;;
  e2e:full) e2e_full ;;
  migrations:full) migrations_full ;;
  changed:quick | changed:full) changed ;;
  branch:quick | branch:full) branch ;;
  file:full) usage ;; # falta la ruta
  file:*) file_check "$mode" ;; # acá $2 es la ruta, no el modo
  *) usage ;;
esac
