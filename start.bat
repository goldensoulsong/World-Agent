@echo off
title Worldbook Agent CLI
echo ===================================
echo     欢迎使用 Worldbook Agent
echo ===================================
echo.
echo 正在检查环境配置，请稍候...
echo.

:: 1. 优先尝试使用 uv（最高速模式）
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [系统提示] 检测到已安装 uv，正在使用高速模式启动...
    uv run main.py
    goto end
)

:: 2. 如果没有 uv，降级为使用普通 Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [错误] 您的电脑既没有安装 uv，也没有安装 Python 环境！
    echo 请前往 https://www.python.org/ 下载并安装 Python 3.10 以上版本。
    pause
    exit /b 1
)

echo [系统提示] 未检测到 uv，将使用系统自带的 Python 运行。
echo 首次运行可能需要下载依赖库，请耐心等待...

:: 检查并创建原生的虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [系统提示] 正在为您创建 Python 隔离环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 升级 pip 并安装 requirements.txt 里的依赖
python -m pip install --upgrade pip >nul 2>nul
echo [系统提示] 正在检查必要的运行库（如 openai 等）...
pip install -r requirements.txt >nul 2>nul

echo.
echo 依赖环境准备完毕，正在启动 Agent...
echo ===================================
python main.py

:end
echo.
echo 程序已退出。
pause
