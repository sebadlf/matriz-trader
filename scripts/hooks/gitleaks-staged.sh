#!/usr/bin/env bash
# Guard de lefthook (AC-12): busca secretos en lo stageado. Cada hallazgo muestra `File:` y `Line:`;
# `--redact` evita imprimir el secreto en la terminal.
set -euo pipefail

command -v gitleaks >/dev/null 2>&1 || {
  echo "Falta gitleaks: brew install gitleaks (ver README «Calidad y tests»)" >&2
  exit 1
}
exec gitleaks git --pre-commit --staged --redact --verbose
