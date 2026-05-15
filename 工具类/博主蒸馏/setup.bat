@echo off
chcp 65001 >nul
title 博主蒸馏器 — 安装向导
echo ============================================================
echo   📦 博主蒸馏器 — 环境自动安装
echo ============================================================
echo.

:: -------- 1. 检查 Python --------
echo [1/4] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python！请先安装 Python 3.10+：https://www.python.org/downloads/
    echo    安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo ✅ Python 已安装
echo.

:: -------- 2. 检查 Node.js --------
echo [2/4] 检查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 未找到 Node.js！Spider_XHS 需要 Node.js 生成签名。
    echo    下载：https://nodejs.org/ （安装 LTS 版本即可）
    echo.
    echo    按任意键继续（后续可手动安装）...
    pause >nul
) else (
    node --version
    echo ✅ Node.js 已安装
)
echo.

:: -------- 3. 安装 Spider_XHS Node.js 依赖 --------
echo [3/4] 安装 Spider_XHS 依赖...
if exist "spider_xhs\package.json" (
    cd spider_xhs
    call npm install --production 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️ npm install 有警告，但不影响核心功能
    ) else (
        echo ✅ Spider_XHS 依赖已安装
    )
    cd ..
) else (
    echo ⚠️ 未找到 spider_xhs/package.json，跳过 Node.js 依赖安装
)
echo.

:: -------- 4. 安装 Python 依赖 --------
echo [4/4] 安装 Python 包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ pip install 失败
    pause
    exit /b 1
)
echo.

:: -------- 配置指引 --------
echo ============================================================
echo ✅ 安装完成！
echo ============================================================
echo.
echo 下一步：配置小红书 Cookie
echo.
echo   1. 登录 https://www.xiaohongshu.com
echo   2. F12 打开开发者工具 → Network
echo   3. 刷新页面，复制任意请求的 Cookie 值
echo   4. 编辑 spider_xhs/.env，写入：
echo      COOKIES=你的完整Cookie值
echo.
echo 启动方式：
echo   python app.py          — 打开 Web 界面
echo   python run.py "博主名" — 命令行一键运行
echo.
echo 按任意键退出...
pause >nul
