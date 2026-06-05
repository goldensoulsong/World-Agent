@echo off
title World-Agent Web Server
echo ===================================
echo     Welcome to World-Agent Nexus
echo ===================================
echo.
echo Checking environment and starting server...
echo.

:: Automatically open browser
echo [System] Waking up browser...
start http://127.0.0.1:8080/static/index.html

:: 1. Try to use uv (high speed mode) first
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [System] uv detected, starting Web server in high-performance mode...
    uv run server.py
    goto end
)

:: 2. If there is no uv, fallback to normal Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [Error] Your computer has neither uv nor a Python environment installed!
    echo Please go to https://www.python.org/ to download and install Python 3.10 or above.
    pause
    exit /b 1
)

echo [System] uv not detected, will use system Python.

:: Check and create native virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [System] Creating Python isolated environment for you...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install FastAPI dependencies if not installed
echo [System] Checking Web dependencies...
pip install fastapi uvicorn python-multipart >nul 2>nul
pip install -r requirements.txt >nul 2>nul

echo.
echo Server is ready, igniting...
echo ===================================
python server.py

:end
echo.
echo Server has been shut down.
pause
