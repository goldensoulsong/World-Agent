@echo off
title World-Agent CLI
echo ===================================
echo     Welcome to World-Agent
echo ===================================
echo.
echo Checking environment configuration, please wait...
echo.

:: 1. Try to use uv (high speed mode) first
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [System] Detected uv installed, starting in high-speed mode...
    uv run main.py
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

echo [System] uv not detected, will run using system Python.
echo First run might need to download dependencies, please be patient...

:: Check and create native virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [System] Creating Python isolated environment for you...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Upgrade pip and install dependencies in requirements.txt
python -m pip install --upgrade pip >nul 2>nul
echo [System] Checking necessary libraries (like openai, etc.)...
pip install -r requirements.txt >nul 2>nul

echo.
echo Dependency environment is ready, starting Agent...
echo ===================================
python main.py

:end
echo.
echo Program has exited.
pause
