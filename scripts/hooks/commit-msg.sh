#!/usr/bin/env bash
# Hook commit-msg de lefthook (AC-13): exige Conventional Commits en la primera línea.
# Uso: scripts/hooks/commit-msg.sh <archivo-del-mensaje>
set -euo pipefail
# `${#first}` cuenta caracteres (no bytes) solo con un locale UTF-8.
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

msg_file="${1:?Uso: scripts/hooks/commit-msg.sh <archivo-del-mensaje>}"
first="$(head -n1 "$msg_file")"
first="${first%$'\r'}"

# Mensajes que genera git (merge, revert, autosquash): se aceptan tal cual.
git_generated='^(Merge|Revert|fixup!|squash!) '
[[ "$first" =~ $git_generated ]] && exit 0

re='^(feat|fix|chore|docs|refactor|test|perf|ci|build)(\([a-z0-9-]+\))?!?: .+$'
if [[ ! "$first" =~ $re ]] || ((${#first} > 72)); then
  echo "Mensaje inválido: «${first}»" >&2
  echo "Formato: <tipo>(<scope>)?: <descripción>, primera línea de hasta 72 caracteres." >&2
  echo "Tipos: feat|fix|chore|docs|refactor|test|perf|ci|build. Ejemplo: feat(backend): agrega Clock inyectable" >&2
  exit 1
fi
