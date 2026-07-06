# =============================================================================
# PanelAgent — Windows 首次环境准备脚本 (PowerShell)
# =============================================================================
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
#
# 完成内容：
#   1. 创建 Python 虚拟环境 .venv
#   2. 安装后端依赖 (backend/requirements.txt + 根 requirements.txt)
#   3. 安装前端依赖 (frontend/)
#   4. 复制 .env.example → .env（若不存在）
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== PanelAgent Windows 环境准备 ===" -ForegroundColor Cyan

# ---- 检查 Python / Node ----
foreach ($cmd in @("python", "node", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "✗ 未找到 $cmd，请先安装 Python 3.13+ 和 Node.js 20+。" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✓ python / node / npm 均已安装" -ForegroundColor Green

# ---- 1. Python 虚拟环境 ----
if (-not (Test-Path ".venv")) {
    Write-Host "[1/4] 创建 Python 虚拟环境 .venv ..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "[1/4] .venv 已存在，跳过" -ForegroundColor Gray
}

& .venv\Scripts\Activate.ps1

# ---- 2. 安装后端依赖 ----
Write-Host "[2/4] 安装后端依赖..." -ForegroundColor Yellow
python -m pip install --upgrade pip
if (Test-Path "requirements.txt") { pip install -r requirements.txt }
pip install -r backend\requirements.txt

# ---- 3. 安装前端依赖 ----
Write-Host "[3/4] 安装前端依赖..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

# ---- 4. .env ----
Write-Host "[4/4] 准备 .env ..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ 已从 .env.example 复制为 .env，请按需修改。" -ForegroundColor Green
} else {
    Write-Host "✓ .env 已存在，跳过" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== 环境准备完成 ===" -ForegroundColor Green
Write-Host "下一步：运行 scripts\start-windows.ps1 启动项目。" -ForegroundColor Cyan
