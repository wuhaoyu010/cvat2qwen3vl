@echo off
title cvat2qwen3vl - Production Mode

set "PROJECT_DIR=%~dp0"
set "PREFERRED_PORT=8001"

echo ============================================
echo   cvat2qwen3vl Production Mode
echo ============================================
echo.

:: Check Python venv
if not exist "%PROJECT_DIR%.venv\Scripts\activate.bat" (
    echo [ERROR] Python venv not found: .venv
    pause
    exit /b 1
)

:: Activate venv
call "%PROJECT_DIR%.venv\Scripts\activate.bat"

:: Add uv to PATH if available
if exist "C:\Users\wuhao\.local\bin\uv.exe" (
    set "PATH=C:\Users\wuhao\.local\bin;%PATH%"
)

:: Configure pnpm Alibaba mirror
pnpm config set registry https://registry.npmmirror.com 2>nul
set "npm_config_registry=https://registry.npmmirror.com"

:: Build frontend if dist missing
if not exist "%PROJECT_DIR%web\dist\index.html" (
    echo [1/2] Building frontend...
    cd /d "%PROJECT_DIR%web"
    pnpm build --network-timeout 300000 --fetch-timeout 120000
    if errorlevel 1 (
        echo [ERROR] Frontend build failed
        pause
        exit /b 1
    )
    echo.
) else (
    echo [INFO] Frontend already built, skipping (delete web\dist to rebuild)
    echo.
)

:: Clean old port file
del "%PROJECT_DIR%.backend_port" 2>nul

echo [2/2] Starting server (auto-detect port)...
echo.

:: Start server
cd /d "%PROJECT_DIR%"
start "cvat2qwen3vl-server" cmd /k "call .venv\Scripts\activate.bat && python -m server.main %PREFERRED_PORT%"

:: Wait for .backend_port file
set WAIT=0
:wait_loop
if exist "%PROJECT_DIR%.backend_port" goto port_ready
if %WAIT% GEQ 50 goto port_timeout
timeout /t 1 /nobreak >nul
set /a WAIT+=1
goto wait_loop

:port_timeout
echo [ERROR] Server startup timeout
taskkill /fi "WINDOWTITLE eq cvat2qwen3vl-server" /f >nul 2>&1
pause
exit /b 1

:port_ready
set /p PORT=<"%PROJECT_DIR%.backend_port"

echo   URL:       http://localhost:%PORT%
echo   API Docs:  http://localhost:%PORT%/docs
echo   Press Ctrl+C to stop
echo ------------------------------------------------

:: Keep current window open
pause
