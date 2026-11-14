<#
.SYNOPSIS
  Script de automatización de ramas y worktrees de Git para el enjambre de agentes en Herdr.
.DESCRIPTION
  Crea las ramas aisladas para cada agente y, opcionalmente, carpetas de trabajo independientes (worktrees)
  para que todos los agentes puedan programar en paralelo sin bloqueos de git ni colisiones.
#>

param (
    [string]$Mode = "branches" # "branches" o "worktrees"
)

Write-Host "Configurando entorno Git para el Enjambre Herdr (NASA Space Apps)..." -ForegroundColor Cyan

# Asegurar commit inicial
git add .
git commit -m "feat: initial system architecture, stats engine, api, ui and datasets" 2>$null

# Lista de ramas para cada perfil de agente
$branches = @(
    "feature/stats",     # Antigravity 1 (Local)
    "feature/api",       # Antigravity 2 (Remoto 192.168.18.24)
    "feature/ui",        # Claude Omni 1 (Local)
    "feature/wizard",    # Claude Omni 2 (Local)
    "feature/etl",       # Claude Omni 3 (Remoto 192.168.18.24)
    "feature/catalog",   # Hermes 1 (Local)
    "feature/scrapes"    # Hermes 2 (Remoto 192.168.18.24)
)

foreach ($b in $branches) {
    # Verificar si la rama ya existe
    $exists = git branch --list $b
    if (-not $exists) {
        git branch $b
        Write-Host "  [OK] Rama creada: $b" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Rama ya existente: $b" -ForegroundColor Yellow
    }
}

if ($Mode -eq "worktrees") {
    Write-Host "`nCreando worktrees independientes para aislamiento físico..." -ForegroundColor Cyan
    $worktreeMap = @{
        "../nasa-stats"     = "feature/stats"
        "../nasa-api"       = "feature/api"
        "../nasa-ui"        = "feature/ui"
        "../nasa-wizard"    = "feature/wizard"
        "../nasa-etl"       = "feature/etl"
        "../nasa-catalog"   = "feature/catalog"
        "../nasa-scrapes"   = "feature/scrapes"
    }

    foreach ($path in $worktreeMap.Keys) {
        $branch = $worktreeMap[$path]
        if (-not (Test-Path $path)) {
            git worktree add $path $branch
            Write-Host "  [OK] Worktree creado en $path vinculado a $branch" -ForegroundColor Green
        }
    }
}

Write-Host "`nEntorno listo. Fable puede supervisar desde la rama main." -ForegroundColor Cyan
