@echo off
REM =============================================================================
REM PanelAgent - Windows one-click start (cmd batch)
REM =============================================================================
REM Double-click this file, or run from cmd:
REM   scripts\start-windows.bat
REM
REM Prerequisites: run scripts\setup-windows.ps1 first (creates venv + deps).
REM =============================================================================

setlocal
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo === PanelAgent Windows 启动 ===

echo [1/2] 启动后端 (端口 8000)...
start "PanelAgent Backend" cmd /k "cd /d "%PROJECT_ROOT%" && set PYTHONPATH=. && call .venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

echo [2/2] 启动前端 (端口 3000)...
start "PanelAgent Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && npm run dev"

echo.
echo 已在新窗口启动后端与前端。
echo   后端 API:  http://127.0.0.1:8000/api/v1/health
echo   前端页面:  http://127.0.0.1:3000
echo.
echo 3 秒后打开浏览器...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:3000

endlocal
