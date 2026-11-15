# SI-assisted: claude-omni-1 (Claude Opus 5.5)
# Script de despliegue continuo (frontend estatico + backend cloud)
# Uso: .\scripts\deploy_update.ps1

param(
    [switch]$SkipGate = $false
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " EarthTrend Detective — Actualizacion y Despliegue" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Puerta de calidad
if (-not $SkipGate) {
    Write-Host "`n[1/3] Verificando calidad con gate.py..." -ForegroundColor Yellow
    python scripts/gate.py --offline --skip-suite
    if ($LASTEXITCODE -ne 0) {
        Write-Error "La puerta de calidad fallo. Corrige los errores antes de desplegar."
        exit 1
    }
} else {
    Write-Host "`n[1/3] Omitiendo gate.py (--SkipGate)..." -ForegroundColor DarkGray
}

# 2. Reconstruir frontend estatico
Write-Host "`n[2/3] Compilando frontend estatico (dist/)..." -ForegroundColor Yellow
python scripts/build_static.py --from-cases
if ($LASTEXITCODE -ne 0) {
    Write-Error "Fallo la compilacion de dist/."
    exit 1
}

# 3. Empujar cambios a GitHub
Write-Host "`n[3/3] Sincronizando ramas 'main' y 'gh-pages'..." -ForegroundColor Yellow
git push origin main

$tempDeploy = Join-Path $env:TEMP "gh-pages-sync"
if (Test-Path $tempDeploy) { Remove-Item -Recurse -Force $tempDeploy }

try {
    git clone --depth 1 --branch gh-pages (git remote get-url origin) $tempDeploy
    Copy-Item -Recurse -Force (Join-Path $ROOT "dist\*") "$tempDeploy/"
    Copy-Item -Force (Join-Path $ROOT "dist\.nojekyll") "$tempDeploy/"

    $status = git -C $tempDeploy status --porcelain
    if ($status) {
        git -C $tempDeploy add -A
        git -C $tempDeploy commit -m "deploy: sync static backup from main ($(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))"
        git -C $tempDeploy push origin gh-pages
        Write-Host "gh-pages actualizado en GitHub Pages." -ForegroundColor Green
    } else {
        Write-Host "gh-pages ya esta al dia." -ForegroundColor Green
    }
} finally {
    if (Test-Path $tempDeploy) { Remove-Item -Recurse -Force $tempDeploy }
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " DESPLIEGUE ACTUALIZADO CON EXITO" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " URL Publica (Frontend): https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./" -ForegroundColor White
Write-Host " GitHub (Backend sync):   https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-." -ForegroundColor White
Write-Host "==========================================================`n" -ForegroundColor Green
