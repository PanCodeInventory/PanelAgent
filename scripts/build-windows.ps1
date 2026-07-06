# =============================================================================
# PanelAgent — Local Windows exe build script (PowerShell)
# =============================================================================
# Produces dist\panelagent.exe: a single-file launcher that runs the backend
# and serves the static frontend from http://127.0.0.1:8000.
#
# Prereqs (run once):
#   - Python 3.13+ in PATH (or an activated venv with the backend deps)
#   - Node.js 20+ in PATH
#   - Run: pip install -r backend\requirements.txt pyinstaller
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== PanelAgent Windows build ===" -ForegroundColor Cyan

# ---- 1. Build the static frontend ----
Write-Host "[1/3] Building static frontend (export mode)..." -ForegroundColor Yellow
Push-Location frontend
# Static-export flags: enable output:export in next.config.ts and point the
# browser straight at the backend (no Next.js proxy route in export mode).
$env:PANELAGENT_STATIC_EXPORT = "1"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
# The proxy route handler is incompatible with output: export.
# Remove it for this build only (kept in the repo for Linux server deploys).
Remove-Item -Recurse -Force "src\app\api" -ErrorAction SilentlyContinue
npm install
npm run build
if (-not (Test-Path "out\index.html")) {
    Write-Host "✗ next build did not produce out\index.html." -ForegroundColor Red
    exit 1
}
Pop-Location
Write-Host "✓ Frontend built to frontend\out" -ForegroundColor Green

# ---- 2. Install build deps ----
Write-Host "[2/3] Ensuring PyInstaller is installed..." -ForegroundColor Yellow
python -m pip install --upgrade pyinstaller
python -m pip install -r backend\requirements.txt

# ---- 3. Build the exe ----
Write-Host "[3/3] Building panelagent.exe via PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller panelagent.spec --noconfirm --clean

if (-not (Test-Path "dist\panelagent.exe")) {
    Write-Host "✗ Build failed: dist\panelagent.exe not found." -ForegroundColor Red
    exit 1
}

$size = [math]::Round((Get-Item "dist\panelagent.exe").Length / 1MB, 1)
Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "  dist\panelagent.exe  ($size MB)" -ForegroundColor Green
Write-Host ""
Write-Host "Smoke test:" -ForegroundColor Cyan
Write-Host "  .\dist\panelagent.exe   (opens browser to http://127.0.0.1:8000)" -ForegroundColor Gray
