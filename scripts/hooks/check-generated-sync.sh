#!/usr/bin/env bash
# Guard de lefthook (AC-11): aborta el commit si frontend/src/api/generated/ está stageado sin
# backend/openapi.json. El cliente Orval sale del contrato versionado; nunca se edita a mano.
set -euo pipefail

staged="$(git diff --cached --name-only)"
if grep -q '^frontend/src/api/generated/' <<<"$staged" && ! grep -qx 'backend/openapi.json' <<<"$staged"; then
  echo "frontend/src/api/generated/ cambió sin backend/openapi.json." >&2
  echo "Flujo para cambiar el contrato (frontend/CLAUDE.md, «Flujo para cambiar el contrato»):" >&2
  echo "  1. cd backend && uv run python -m app.scripts.export_openapi" >&2
  echo "  2. cd frontend && vp run generate:api" >&2
  echo "  3. commiteá juntos backend/openapi.json y frontend/src/api/generated/" >&2
  exit 1
fi
