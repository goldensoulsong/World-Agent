@echo off
title World-Agent Nexus
echo ===================================
echo     Welcome to World-Agent Nexus
echo ===================================
echo.
echo Starting Python Backend on Port 8080...
echo.

:: Automatically open browser
echo [System] Waking up browser...
start http://127.0.0.1:8080/static/index.html

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run server.py
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [Error] Your computer has neither uv nor a Python environment installed!
        pause
        exit /b 1
    )
    if not exist ".venv\Scripts\activate.bat" (
        echo [System] Creating Python isolated environment for you...
        python -m venv .venv
    )
    call .venv\Scripts\activate.bat && pip install -e . >nul 2>nul && python server.py
)
pause
