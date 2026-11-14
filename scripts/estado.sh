#!/usr/bin/env bash
# SI-assisted: cfable (Claude Fable 5.2)
# Imprime el bloque ESTADO de cada agente, leyendo de main y de todas las ramas remotas, sin tocar el árbol de trabajo.
# Uso: bash scripts/estado.sh
set -u
git fetch origin --prune --quiet
for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v -E 'HEAD|^origin$'); do
  for f in $(git ls-tree --name-only "$ref" reports/ 2>/dev/null | grep -E '\.md$' | grep -v README); do
    bloque=$(git show "$ref:$f" | sed -n '/ESTADO:INICIO/,/ESTADO:FIN/p' | grep -v 'ESTADO:')
    if [ -n "$bloque" ]; then
      echo "=== $f @ $ref ($(git rev-parse --short "$ref"))"
      echo "$bloque"
      echo
    fi
  done
done | awk '!seen[$0]++ || $0==""'
echo "--- sin bloque ESTADO todavía:"
for a in antigravity-1 antigravity-2 claude-omni-1 claude-omni-2 claude-omni-3 hermes-1 hermes-2; do
  n=$(for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v -E 'HEAD|^origin$'); do git show "$ref:reports/$a.md" 2>/dev/null | grep -c 'ESTADO:INICIO'; done | awk '{s+=$1} END {print s+0}')
  [ "$n" = "0" ] && echo "  $a"
done
exit 0
