#!/usr/bin/env bash
# Uso: scripts/verify-guards.sh <backend|frontend>
#
# Verifica que los gates de verdad fallan: copia cada probe de scripts/guard-probes/<módulo>/<probe>/
# (un árbol que replica la raíz del módulo) dentro del módulo, corre la herramienta que debe
# rechazarlo y exige exit distinto de 0 más cada texto esperado en la salida (AC-21, AC-22, AC-24,
# AC-27, AC-28, AC-30). Los archivos copiados se llaman `_probe*` (ignorados por git) y se borran
# después de cada probe y al salir, incluso si se interrumpe el script.
#
# Compatible con el bash 3.2 de macOS. La invoca scripts/gate.sh en modo full.
set -euo pipefail
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
module="${1:-}"
case "$module" in
  backend) SRC_DIR="app" ;;
  frontend) SRC_DIR="src" ;;
  *) echo "Uso: scripts/verify-guards.sh <backend|frontend>" >&2; exit 64 ;;
esac
MOD="$ROOT/$module"
PROBES="$ROOT/scripts/guard-probes/$module"

cleanup() { find "$MOD/$SRC_DIR" -name '_probe*' -prune -exec rm -rf {} + 2>/dev/null || true; }
trap cleanup EXIT INT TERM
cleanup

failures=0

# run_probe <probe> <texto esperado>... -- <comando>...
# En el comando, el argumento literal `{files}` se reemplaza por los archivos del probe
# (rutas relativas al módulo): las herramientas que descubren archivos respetan .gitignore y
# no verían un `_probe*` si no se lo pasa explícitamente.
run_probe() {
  local name="$1"; shift
  local expected=()
  while [[ $# -gt 0 && "$1" != "--" ]]; do expected+=("$1"); shift; done
  shift # el `--`
  local src="$PROBES/$name"
  if [[ ! -d "$src" ]]; then
    echo "✗ $module/$name: no existe $src" >&2; failures=$((failures + 1)); return 0
  fi

  local files; files="$(cd "$src" && find . -type f | sed 's|^\./||' | sort)"
  cp -R "$src/." "$MOD/"

  local cmd=() arg f
  for arg in "$@"; do
    if [[ "$arg" == "{files}" ]]; then
      while IFS= read -r f; do cmd+=("$f"); done <<<"$files"
    else
      cmd+=("$arg")
    fi
  done

  local out rc=0
  out="$(cd "$MOD" && "${cmd[@]}" 2>&1)" || rc=$?
  cleanup

  local problems=() text
  [[ "$rc" -ne 0 ]] || problems+=("la herramienta salió con 0")
  for text in "${expected[@]}"; do
    grep -qF -- "$text" <<<"$out" || problems+=("falta «${text}» en la salida")
  done

  if [[ ${#problems[@]} -eq 0 ]]; then
    echo "✓ $module/$name → ${cmd[*]} (exit $rc)"
  else
    failures=$((failures + 1))
    echo "✗ $module/$name → ${cmd[*]} (exit $rc)" >&2
    for text in "${problems[@]}"; do echo "    - $text" >&2; done
    echo "    Salida (últimas 40 líneas):" >&2
    tail -n 40 <<<"$out" | sed 's/^/    | /' >&2
  fi
}

if [[ "$module" == "backend" ]]; then
  run_probe utcnow DTZ003 -- uv run ruff check --no-cache {files}
  run_probe naive_now DTZ005 -- uv run ruff check --no-cache {files}
  run_probe async_sleep ASYNC251 -- uv run ruff check --no-cache {files}
  run_probe requests_import TID251 -- uv run ruff check --no-cache {files}
  run_probe domain_imports_fastapi "Dominio puro" "app.domain._probe -> fastapi" -- uv run lint-imports --no-cache
  run_probe api_imports_db "API sin acceso directo a la DB" "app.api.routes._probe -> app.db" -- uv run lint-imports --no-cache
else
  run_probe raw-fetch no-restricted-globals no-restricted-properties -- vp lint {files}
  run_probe axios no-restricted-imports -- vp lint {files}
  run_probe enum TS1294 -- vp check {files}
  run_probe deep-relative no-restricted-imports -- vp lint {files}
  run_probe screen-to-screen screen-no-otra-screen \
    "src/screens/_probeA/index.ts → src/screens/HomeScreen/index.ts" -- vp run lint:arch
  run_probe component-to-api components-limites \
    "src/components/_probe.tsx → src/api/queryClient.ts" -- vp run lint:arch
  run_probe cycle no-circular "src/utils/_probeA.ts" "src/utils/_probeB.ts" -- vp run lint:arch
  run_probe hook-to-component hooks-limites \
    "src/hooks/_probe.ts → src/components/_probeComp.tsx" -- vp run lint:arch
  run_probe utils-to-api utils-constants-puros \
    "src/utils/_probe.ts → src/api/queryClient.ts" -- vp run lint:arch
  run_probe layout-to-screen-internal screen-via-index \
    "src/layouts/_probe.tsx → src/screens/HomeScreen/HomeScreen.tsx" -- vp run lint:arch
fi

if [[ "$failures" -gt 0 ]]; then
  echo "verify-guards $module: $failures probe(s) no fallaron como se esperaba." >&2
  exit 1
fi
echo "verify-guards $module: todos los probes fallaron con la regla esperada."
