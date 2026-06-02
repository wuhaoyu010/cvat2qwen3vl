@echo off
title cvat2qwen3vl - Production Mode

set "PROJECT_DIR=%~dp0"
set "PORT=8001"

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
    pnpm build 
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

echo [2/2] Starting server...
echo.
echo   URL:       http://localhost:%PORT%
echo   API Docs:  http://localhost:%PORT%/docs
echo   Press Ctrl+C to stop
echo ------------------------------------------------

cd /d "%PROJECT_DIR%"
uvicorn server.main:app --host 0.0.0.0 --port %PORT%
