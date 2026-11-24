#!/usr/bin/env bash
# Hook Stop de Claude Code (AC-16, AC-17): antes de que el agente termine el turno, corre el gate
# `full` de cada módulo con cambios sin commitear (`scripts/gate.sh changed full`). Si falla,
# impide terminar (exit 2) y le devuelve al agente las últimas 120 líneas de la salida.
set -euo pipefail

command -v jq >/dev/null 2>&1 || { echo "Falta 'jq': instalalo con 'brew install jq'." >&2; exit 2; }

# AC-17: si el turno ya fue retenido por este hook, no se vuelve a correr el gate (evita loops).
if [[ "$(jq -r '.stop_hook_active // false')" == "true" ]]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
log="$(mktemp)"
trap 'rm -f "$log"' EXIT

if ! "$ROOT/scripts/gate.sh" changed full >"$log" 2>&1; then
  {
    echo "El gate de los módulos modificados falló (scripts/gate.sh changed full). Corregí los errores antes de terminar:"
    tail -n 120 "$log"
  } >&2
  exit 2
fi
exit 0
