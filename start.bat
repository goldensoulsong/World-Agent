@echo off
title World-Agent Nexus Deployment Tool
color 0A

echo ========================================================
echo.
echo      🚀 World-Agent Nexus (v0.1) Launcher 🚀
echo.
echo ========================================================
echo.
echo Please select your deployment environment:
echo.
echo   [1] Docker Mode (Recommended, auto-configures PostgreSQL)
echo   [2] Local Mode (Requires Node.js and Python installed)
echo.

set /p choice="Enter 1 or 2 and press Enter: "

if "%choice%"=="1" goto docker_mode
if "%choice%"=="2" goto local_mode

echo Invalid input. Please run the script again.
pause
exit /b

:docker_mode
echo.
echo [System] Checking Docker environment...
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] Docker not found! Please install Docker Desktop and ensure it is running.
    echo If you don't want to use Docker, rerun this script and select [2] Local Mode.
    pause
    exit /b 1
)

echo [System] Starting Docker containers (this may take a while to pull images)...
docker-compose up -d --build

if %ERRORLEVEL% equ 0 (
    echo.
    echo [Success] Containers started successfully!
    echo [System] Waking up browser...
    start http://127.0.0.1:8080/static/index.html
) else (
    color 0C
    echo [Error] Failed to start Docker containers. Please check if Docker daemon is running.
)
pause
exit /b

:local_mode
echo.
echo [System] Checking local environment...
echo.

:: 1. Check Node.js and build frontend
echo [Step 1/3] Checking frontend environment (Node.js)...
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] npm not found! Node.js is required to build the frontend in local mode.
    echo Please download and install it from https://nodejs.org/
    pause
    exit /b 1
)

echo [System] Building React frontend (this may take 1-2 minutes)...
cd frontend
call npm install
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] npm install failed! Please check your network connection.
    pause
    exit /b 1
)
call npm run build
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] Frontend build failed!
    pause
    exit /b 1
)
cd ..
echo [Success] Frontend built successfully!
echo.

:: 2. Check Python environment and install dependencies
echo [Step 2/3] Checking backend environment (Python / uv)...
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [System] 'uv' detected, syncing dependencies...
    uv sync
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [Error] uv sync failed!
        pause
        exit /b 1
    )
    echo [Step 3/3] Starting backend service...
    start http://127.0.0.1:8080/static/index.html
    uv run server.py
    exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] Python not found! Please install from https://www.python.org/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [System] Creating Python virtual environment...
    python -m venv .venv
)

echo [System] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
pip install -e . >nul 2>nul
echo [Success] Backend dependencies are ready!
echo.

:: 3. Start
echo [Step 3/3] Starting backend service...
echo [System] Waking up browser...
start http://127.0.0.1:8080/static/index.html
python server.py

pause
