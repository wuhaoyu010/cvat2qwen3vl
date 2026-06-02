@echo off
title cvat2qwen3vl - Dev Mode

set "PROJECT_DIR=%~dp0"
set "BACKEND_PORT=8001"
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

:: Check node_modules
if not exist "%PROJECT_DIR%web\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd /d "%PROJECT_DIR%web"
    pnpm install
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

echo [1/2] Starting backend (port %BACKEND_PORT%)...
echo [2/2] Starting frontend (port %FRONTEND_PORT%)...
echo.
echo   Backend:  http://localhost:%BACKEND_PORT%
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   Press Ctrl+C to stop all services
echo ------------------------------------------------

:: Start backend in new window
start "cvat2qwen3vl-backend" cmd /k "cd /d %PROJECT_DIR% && title Backend-FastAPI-%BACKEND_PORT% && call .venv\Scripts\activate.bat && uvicorn server.main:app --reload --port %BACKEND_PORT%"

:: Wait for backend to start
timeout /t 2 /nobreak >nul

:: Start frontend in current window
cd /d "%PROJECT_DIR%web"
pnpm dev

:: Kill backend when frontend exits
taskkill /fi "WINDOWTITLE eq Backend-FastAPI-%BACKEND_PORT%" /f >nul 2>&1
