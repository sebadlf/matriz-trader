#!/usr/bin/env bash
# Verifica que los Dockerfiles y `engines.node` usen las versiones fijadas en
# `.python-version` y `.nvmrc` (AC-40). Sale con código distinto de 0 si alguna no coincide.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python_version="$(tr -d '[:space:]' < .python-version)"
node_version="$(tr -d '[:space:]' < .nvmrc)"
failures=0

fail() {
  echo "FAIL: $1" >&2
  failures=$((failures + 1))
}

shopt -s nullglob
for dockerfile in */Dockerfile; do
  while read -r image; do
    tag="${image#*:}"
    case "$image" in
      python:*)
        [[ "$tag" == "$python_version" || "$tag" == "$python_version"-* ]] \
          || fail "$dockerfile usa $image, se esperaba python:$python_version (.python-version)"
        ;;
      node:*)
        [[ "$tag" == "$node_version" || "$tag" == "$node_version"-* ]] \
          || fail "$dockerfile usa $image, se esperaba node:$node_version (.nvmrc)"
        ;;
    esac
  done < <(awk 'toupper($1) == "FROM" { print $2 }' "$dockerfile")
done

engines_node="$(sed -n 's/^[[:space:]]*"node":[[:space:]]*"\([^"]*\)".*/\1/p' frontend/package.json | head -n 1)"
[[ "$engines_node" == ">=$node_version <$((node_version + 1))" ]] \
  || fail "frontend/package.json engines.node es '$engines_node', se esperaba '>=$node_version <$((node_version + 1))' (.nvmrc)"

if ((failures > 0)); then
  exit 1
fi
echo "OK: Python $python_version y Node $node_version coinciden en Dockerfiles y engines.node"
