@echo off
setlocal enabledelayedexpansion

echo.
echo  ==========================================
echo    XHS Toolbox - Setup
echo  ==========================================
echo.

:: -- Check Python --
echo [1/4] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Python not found!
    echo.
    echo   Please install Python 3.10+:
    echo   https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: Check "Add Python to PATH" during install!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo   [OK] %PY_VER%
echo.

:: -- Install Python deps --
echo [2/4] Installing Python packages...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo   Tsinghua mirror failed, trying default...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo   [ERROR] Python packages install failed, check network
        pause
        exit /b 1
    )
)
echo   [OK] Python packages installed
echo.

:: -- Check Node.js --
echo [3/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] Node.js not found
    echo   XHS API encryption requires Node.js:
    echo   https://nodejs.org/  Download LTS version
    echo.
    echo   Skipping npm install. Re-run this script after installing Node.js
    echo.
) else (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
    echo   [OK] Node %NODE_VER%
    echo   Installing Spider_XHS deps...
    cd 工具类\博主蒸馏\spider_xhs
    call npm install --registry=https://registry.npmmirror.com >nul 2>&1
    if %errorlevel% neq 0 (
        call npm install >nul 2>&1
    )
    cd ..\..\..
    echo   [OK] Spider_XHS deps installed
)
echo.

:: -- Config .env --
echo [4/4] Checking config...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo   [OK] Created .env from template
    ) else (
        echo   [WARN] .env.example not found, please create .env manually
    )
) else (
    echo   [OK] .env already exists
)
echo.

:: -- Check Cookie --
findstr /C:"your_cookie_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo   [WARN] Cookie not configured in .env
    echo   Please edit .env and replace your_cookie_here with your XHS Cookie
    echo.
    echo   How to get Cookie:
    echo   1. Login https://www.xiaohongshu.com
    echo   2. Press F12 - Network tab - Refresh page
    echo   3. Click any xiaohongshu.com request
    echo   4. Copy Cookie value from Request Headers
    echo.
) else (
    echo   [OK] Cookie configured
)

echo.
echo  ==========================================
echo    Setup Complete!
echo  ==========================================
echo.
echo   Next steps:
echo   1. Edit .env and fill in your XHS Cookie (required)
echo   2. Double-click start.bat to launch
echo   3. Open http://localhost:5001 in browser
echo.
pause
