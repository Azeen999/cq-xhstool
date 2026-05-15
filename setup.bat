@echo off
chcp 65001 >nul
title 小红书工具箱 — 安装脚本

echo ============================================
echo  小红书工具箱 — 一键安装
echo ============================================
echo.

:: 1. 检查 Python
echo [1/4] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.8+
    echo         下载: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

:: 2. 检查 Node.js
echo.
echo [2/4] 检查 Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 未找到 Node.js，爬虫功能将不可用
    echo        下载: https://nodejs.org/
) else (
    node --version
)

:: 3. 安装 Python 依赖
echo.
echo [3/4] 安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARN] pip 安装失败，尝试 pip3...
    pip3 install -r requirements.txt
)

:: 4. 配置 Spider_XHS Cookie
echo.
echo [4/4] Cookie 配置
if not exist "工具类\博主蒸馏\spider_xhs\.env" (
    echo [INFO] 请配置小红书 Cookie:
    echo   1. 浏览器打开 https://www.xiaohongshu.com 并登录
    echo   2. 按 F12 打开开发者工具 -^> 网络(Network)
    echo   3. 刷新页面，找到任意请求，复制 Request Header 中的 Cookie 值
    echo   4. 编辑 工具类\博主蒸馏\spider_xhs\.env 文件
    echo   5. 将 COOKIES= 后面替换为你的 Cookie
    echo.
    echo   也可以现在先跳过，之后手动配置
) else (
    echo [OK] .env 文件已存在
)

echo.
echo ============================================
echo  安装完成！
echo.
echo  启动: python app.py
echo  然后浏览器打开 http://localhost:5001
echo ============================================
pause
