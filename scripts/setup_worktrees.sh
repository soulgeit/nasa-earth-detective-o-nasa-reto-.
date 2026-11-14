#!/usr/bin/env bash
# Script para Linux / Mac / Nodo remoto 192.168.18.24
echo "Configurando ramas de trabajo para el nodo remoto..."

git add .
git commit -m "feat: initial commit for fleet" 2>/dev/null

branches=("feature/stats" "feature/api" "feature/ui" "feature/wizard" "feature/etl" "feature/catalog" "feature/scrapes")

for b in "${branches[@]}"; do
  git branch "$b" 2>/dev/null && echo "  [OK] Rama creada: $b" || echo "  [INFO] Rama ya existe: $b"
done

echo "Listo. Para iniciar en este nodo:"
echo "  Antigravity 2: git checkout feature/api"
echo "  Claude Omni 3: git checkout feature/etl"
echo "  Hermes 2:      git checkout feature/scrapes"
