#!/usr/bin/env bash
# Hook PreToolUse de Claude Code (AC-14): bloquea la edición de archivos generados o protegidos e
# indica cómo regenerarlos. Lee el JSON del hook por stdin; exit 2 bloquea la herramienta y el
# texto de stderr le llega al agente.
set -euo pipefail

command -v jq >/dev/null 2>&1 || {
  echo "Falta 'jq' (prerrequisito de los hooks de .claude/): instalalo con 'brew install jq'." >&2
  exit 2 # fail-closed: sin jq no se puede verificar la ruta
}

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
path="$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"
[[ -n "$path" ]] || exit 0

# Ruta relativa a la raíz del repo; las rutas fuera del repo no se controlan.
case "$path" in
  "$ROOT"/*) rel="${path#"$ROOT"/}" ;;
  /*) exit 0 ;;
  *) rel="${path#./}" ;;
esac

block() { # block <comando para regenerar>
  echo "Archivo generado/protegido: ${rel}. Regeneralo con: $1" >&2
  exit 2
}

case "$rel" in
  frontend/src/api/generated/*)
    block "cd frontend && vp run generate:api (después de cambiar el contrato del backend y exportar openapi.json)" ;;
  backend/openapi.json) block "cd backend && uv run python -m app.scripts.export_openapi" ;;
  backend/uv.lock) block "cd backend && uv lock (o uv add/uv remove)" ;;
  frontend/pnpm-lock.yaml) block "cd frontend && vp install (o vp add/vp remove)" ;;
esac

name="$(basename "$rel")"
if [[ "$name" == ".env" || ("$name" == .env.* && "$name" != ".env.example") ]]; then
  echo "Archivo protegido: ${rel}. Contiene secretos: lo edita una persona. Las variables nuevas van en .env.example." >&2
  exit 2
fi
exit 0
