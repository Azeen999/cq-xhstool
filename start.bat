@echo off
setlocal enabledelayedexpansion

:: -- First run check --
if not exist .env (
    echo.
    echo  [INFO] First time detected, running setup...
    echo.
    call setup.bat
    if %errorlevel% neq 0 exit /b 1
)

:: -- Check Python --
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Python not found, please run setup.bat first
    echo.
    pause
    exit /b 1
)

:: -- Check key dependencies --
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [WARN] Dependencies missing, auto-installing...
    echo.
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
    if %errorlevel% neq 0 (
        python -m pip install -r requirements.txt >nul 2>&1
    )
    python -c "import flask" >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo   [ERROR] Dependency install failed! Please run setup.bat manually
        echo.
        pause
        exit /b 1
    )
    echo   [OK] Dependencies installed
    echo.
)

:: -- Check Cookie --
findstr /C:"your_cookie_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo  ==========================================
    echo    [WARN] Cookie not configured!
    echo  ==========================================
    echo    Please edit .env and fill in your XHS Cookie
    echo.
    echo    How to get Cookie:
    echo    1. Login xiaohongshu.com
    echo    2. F12 - Network - Refresh page
    echo    3. Copy Cookie value from any request
    echo  ==========================================
    echo.
    echo  Press any key to open .env for editing...
    pause >nul
    notepad .env
)

echo.
echo  ==========================================
echo    XHS Toolbox - Starting...
echo  ==========================================
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Startup failed! Common causes:
    echo.
    echo   1. Dependencies not installed
    echo      - Run setup.bat to install
    echo.
    echo   2. Port 5001 already in use
    echo      - Close other programs using port 5001
    echo.
    echo   3. Cookie expired
    echo      - Re-get Cookie and update .env
    echo.
    echo   4. Python version too old
    echo      - Need Python 3.10+
    echo.
    echo   If still not working, screenshot the error above and report
    echo.
    pause
)
