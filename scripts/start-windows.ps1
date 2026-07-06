# =============================================================================
# PanelAgent — Windows 一键启动脚本 (PowerShell)
# =============================================================================
# 用法：
#   1. 右键此脚本 → "使用 PowerShell 运行"
#   2. 或在 PowerShell 中：  powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1
#
# 前置条件（首次运行）：
#   - Python 3.13+：  https://www.python.org/downloads/
#   - Node.js 20+：   https://nodejs.org/
#   - 已执行过 scripts\setup-windows.ps1（创建 venv、安装依赖）
# =============================================================================

param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== PanelAgent Windows 启动 ===" -ForegroundColor Cyan
Write-Host "项目根目录: $ProjectRoot"
Write-Host ""

# ---- 启动后端 ----
Write-Host "[1/2] 启动后端 (端口 $BackendPort)..." -ForegroundColor Yellow
$backendCmd = "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port $BackendPort"
$backendPwsh = "cd `$PWD; `$env:PYTHONPATH='.'; $backendCmd"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendPwsh

# ---- 启动前端 ----
Write-Host "[2/2] 启动前端 (端口 $FrontendPort)..." -ForegroundColor Yellow
$frontendPwsh = "cd `$PWD\frontend; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendPwsh

Write-Host ""
Write-Host "✓ 已在新窗口启动后端与前端。" -ForegroundColor Green
Write-Host "  后端 API:  http://127.0.0.1:$BackendPort/api/v1/health" -ForegroundColor Gray
Write-Host "  前端页面:  http://127.0.0.1:$FrontendPort" -ForegroundColor Gray
Write-Host ""
Write-Host "3 秒后自动打开浏览器..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:$FrontendPort"
