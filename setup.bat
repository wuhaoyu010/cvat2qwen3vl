@echo off
title cvat2qwen3vl - First-Time Setup

set "PROJECT_DIR=%~dp0"

echo ============================================
echo   cvat2qwen3vl First-Time Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 18+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

:: Check pnpm
pnpm --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm --registry https://registry.npmmirror.com
)

:: Configure pnpm Alibaba mirror
echo [INFO] Configuring pnpm mirror...
pnpm config set registry https://registry.npmmirror.com 2>nul
set "npm_config_registry=https://registry.npmmirror.com"

:: Check uv
set "UV_PATH=C:\Users\wuhao\.local\bin\uv.exe"
if not exist "%UV_PATH%" (
    echo [INFO] Installing uv...
    pip install uv
)

:: Create venv
if not exist "%PROJECT_DIR%.venv" (
    echo [1/3] Creating Python venv...
    cd /d "%PROJECT_DIR%"
    python -m venv .venv
)

:: Activate venv
call "%PROJECT_DIR%.venv\Scripts\activate.bat"

:: Add uv to PATH
if exist "%UV_PATH%" (
    set "PATH=C:\Users\wuhao\.local\bin;%PATH%"
)

:: Install Python deps
echo [2/3] Installing Python dependencies...
cd /d "%PROJECT_DIR%"
uv pip install -r requirements.txt
uv pip install fastapi uvicorn[standard] python-multipart websockets

:: Install frontend deps
echo [3/3] Installing frontend dependencies...
cd /d "%PROJECT_DIR%web"
pnpm install  --fetch-timeout 120000

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   Dev mode:  start.bat
echo   Prod mode: start-prod.bat
echo.
pause
