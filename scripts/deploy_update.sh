#!/usr/bin/env bash
# SI-assisted: claude-omni-1 (Claude Opus 5.5)
# Script de despliegue continuo (frontend estático + backend cloud)
# Uso: bash scripts/deploy_update.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=========================================================="
echo " EarthTrend Detective — Actualización y Despliegue"
echo "=========================================================="

echo -e "\n[1/3] Compilando frontend estático (dist/)..."
python scripts/build_static.py --from-cases

echo -e "\n[2/3] Empujando 'main' a GitHub..."
git push origin main

echo -e "\n[3/3] Actualizando 'gh-pages'..."
TEMP_DEPLOY="$(mktemp -d)"
trap 'rm -rf "$TEMP_DEPLOY"' EXIT

git clone --depth 1 --branch gh-pages "$(git remote get-url origin)" "$TEMP_DEPLOY"
cp -r dist/* "$TEMP_DEPLOY/"
touch "$TEMP_DEPLOY/.nojekyll"

if [[ -n "$(git -C "$TEMP_DEPLOY" status --porcelain)" ]]; then
    git -C "$TEMP_DEPLOY" add -A
    git -C "$TEMP_DEPLOY" commit -m "deploy: sync static backup from main ($(date -u +'%Y-%m-%d %H:%M:%S UTC'))"
    git -C "$TEMP_DEPLOY" push origin gh-pages
    echo "gh-pages actualizado en GitHub Pages."
else
    echo "gh-pages ya está al día."
fi

echo -e "\n=========================================================="
echo " DESPLIEGUE ACTUALIZADO"
echo " https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./"
echo "=========================================================="
