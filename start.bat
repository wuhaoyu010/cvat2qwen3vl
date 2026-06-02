@echo off
title cvat2qwen3vl - Dev Mode

set "PROJECT_DIR=%~dp0"
set "PREFERRED_PORT=8001"
set "FRONTEND_PORT=5173"

echo ============================================
echo   cvat2qwen3vl Development Mode
echo ============================================
echo.

:: Check Python venv
if not exist "%PROJECT_DIR%.venv\Scripts\activate.bat" (
    echo [ERROR] Python venv not found: .venv
    echo Run: uv venv .venv ^&^& uv pip install -r requirements.txt
    pause
    exit /b 1
)

:: Configure pnpm Alibaba mirror
pnpm config set registry https://registry.npmmirror.com 2>nul
set "npm_config_registry=https://registry.npmmirror.com"

:: Check node_modules
if not exist "%PROJECT_DIR%web\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd /d "%PROJECT_DIR%web"
    pnpm install --fetch-timeout 120000
    if errorlevel 1 (
        echo [ERROR] Frontend install failed
        pause
        exit /b 1
    )
)

:: Activate venv
call "%PROJECT_DIR%.venv\Scripts\activate.bat"

:: Add uv to PATH if available
if exist "C:\Users\wuhao\.local\bin\uv.exe" (
    set "PATH=C:\Users\wuhao\.local\bin;%PATH%"
)

:: Clean old port file
del "%PROJECT_DIR%.backend_port" 2>nul

echo [1/2] Starting backend (auto-detect port)...
echo [2/2] Starting frontend (port %FRONTEND_PORT%)...
echo.

:: Start backend in new window
start "cvat2qwen3vl-backend" cmd /k "cd /d %PROJECT_DIR% && title Backend && call .venv\Scripts\activate.bat && python -m server.main %PREFERRED_PORT%"

:: Wait for .backend_port file
set WAIT=0
:wait_loop
if exist "%PROJECT_DIR%.backend_port" goto port_ready
if %WAIT% GEQ 50 goto port_timeout
timeout /t 1 /nobreak >nul
set /a WAIT+=1
goto wait_loop

:port_timeout
echo [ERROR] Backend startup timeout
taskkill /fi "WINDOWTITLE eq Backend" /f >nul 2>&1
pause
exit /b 1

:port_ready
set /p BACKEND_PORT=<"%PROJECT_DIR%.backend_port"

echo   Backend:  http://localhost:%BACKEND_PORT%
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   Press Ctrl+C to stop all services
echo ------------------------------------------------

:: Start frontend in current window
cd /d "%PROJECT_DIR%web"
pnpm dev

:: Kill backend when frontend exits
taskkill /fi "WINDOWTITLE eq Backend" /f >nul 2>&1
del "%PROJECT_DIR%.backend_port" 2>nul
