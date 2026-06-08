@echo off
chcp 65001 >nul
title World-Agent Nexus 一键部署工具
color 0A

echo ========================================================
echo.
echo      🚀 World-Agent Nexus (v0.1) 一键部署工具 🚀
echo.
echo ========================================================
echo.
echo 请选择您的运行环境：
echo.
echo   [1] Docker 环境一键启动 (推荐，自动配置 PostgreSQL)
echo   [2] 本地开发环境启动 (需自备 Node.js 和 Python 环境)
echo.

set /p choice="请输入 1 或 2 并按回车: "

if "%choice%"=="1" goto docker_mode
if "%choice%"=="2" goto local_mode

echo 无效的输入，请重新运行。
pause
exit /b

:docker_mode
echo.
echo [System] 正在检查 Docker 环境...
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] 未检测到 Docker！请先安装 Docker Desktop 并在后台运行。
    echo 如果您不想安装 Docker，请重新运行本脚本并选择 [2] 本地模式。
    pause
    exit /b 1
)

echo [System] 正在启动 Docker 容器组 (可能需要拉取镜像，请耐心等待)...
docker-compose up -d --build

if %ERRORLEVEL% equ 0 (
    echo.
    echo [Success] 容器启动成功！
    echo [System] 正在唤醒浏览器...
    start http://127.0.0.1:8080/static/index.html
) else (
    color 0C
    echo [Error] Docker 容器启动失败，请检查 Docker 是否正常运行。
)
pause
exit /b

:local_mode
echo.
echo [System] 开始检测本地运行环境...
echo.

:: 1. 检查 Node.js 并构建前端
echo [Step 1/3] 检查前端环境 (Node.js)...
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] 未检测到 npm 环境！本地模式需要安装 Node.js 才能构建前端。
    echo 请前往 https://nodejs.org/ 下载安装后重试。
    pause
    exit /b 1
)

echo [System] 正在构建前端 React 界面，这可能需要 1-2 分钟...
cd frontend
call npm install
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] npm install 失败！请检查网络或配置淘宝镜像。
    pause
    exit /b 1
)
call npm run build
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] 前端构建失败！
    pause
    exit /b 1
)
cd ..
echo [Success] 前端构建完成！
echo.

:: 2. 检查 Python 环境并安装依赖
echo [Step 2/3] 检查后端环境 (Python / uv)...
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [System] 检测到 uv 环境，正在同步依赖...
    uv sync
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [Error] uv 依赖同步失败！
        pause
        exit /b 1
    )
    echo [Step 3/3] 启动后端服务...
    start http://127.0.0.1:8080/static/index.html
    uv run server.py
    exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [Error] 未检测到 Python 环境！请前往 https://www.python.org/ 安装。
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [System] 正在为您创建 Python 虚拟环境...
    python -m venv .venv
)

echo [System] 正在激活虚拟环境并安装/检查依赖...
call .venv\Scripts\activate.bat
pip install -e . >nul 2>nul
echo [Success] 后端依赖就绪！
echo.

:: 3. 启动
echo [Step 3/3] 启动后端服务...
echo [System] 正在唤醒浏览器...
start http://127.0.0.1:8080/static/index.html
python server.py

pause
