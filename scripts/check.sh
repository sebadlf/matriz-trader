#!/usr/bin/env bash
# Gate de calidad de todo el monorepo (AC-23, AC-24, AC-40, AC-41): lint, formato,
# type-check y unit tests de Python y del frontend. Ejecuta todos los gates y sale
# con código distinto de 0 si alguno falla.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

failed=()

run() {
  local name="$1"
  shift
  echo "==> $name"
  if "$@"; then
    echo "<== $name: OK"
  else
    echo "<== $name: FAIL" >&2
    failed+=("$name")
  fi
}

run "versions" scripts/check-versions.sh

# Python (workspace uv)
run "ruff check" uv run ruff check .
run "ruff format --check" uv run ruff format --check .
run "pyright" uv run pyright
for project in model broker backend worker; do
  run "pytest $project" bash -c "cd '$ROOT/$project' && uv run pytest"
done

# Frontend
run "npm lint" npm --prefix frontend run lint
run "npm format:check" npm --prefix frontend run format:check
run "npm typecheck" npm --prefix frontend run typecheck
run "npm test" npm --prefix frontend run test

if ((${#failed[@]} > 0)); then
  echo "Gates fallidos: ${failed[*]}" >&2
  exit 1
fi
echo "Todos los gates pasaron"
