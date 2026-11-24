#!/usr/bin/env bash
# Hook PostToolUse de Claude Code (AC-15): formatea y lintea el archivo editado. Los comandos viven
# en `scripts/gate.sh file` (AC-19); este hook solo extrae la ruta y traduce el resultado.
# Si queda algún error, lo devuelve al agente por stderr con exit 2.
set -euo pipefail

command -v jq >/dev/null 2>&1 || { echo "Falta 'jq': instalalo con 'brew install jq'." >&2; exit 2; }

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
path="$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"
[[ -n "$path" ]] || exit 0

case "$path" in
  "$ROOT"/*) rel="${path#"$ROOT"/}" ;;
  /*) exit 0 ;;
  *) rel="${path#./}" ;;
esac

case "$rel" in
  frontend/src/api/generated/*) exit 0 ;;
  backend/*.py | frontend/*.ts | frontend/*.tsx) ;;
  *) exit 0 ;;
esac
[[ -f "$ROOT/$rel" ]] || exit 0

if ! out="$("$ROOT/scripts/gate.sh" file "$rel" 2>&1)"; then
  printf 'Quedan errores de formato/lint en %s:\n%s\n' "$rel" "$out" >&2
  exit 2
fi
exit 0
