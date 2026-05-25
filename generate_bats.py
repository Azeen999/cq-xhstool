"""
Generate GBK-encoded .bat files for Chinese Windows compatibility.
UTF-8 .bat files break in CMD because CMD reads them as GBK by default,
and chcp 65001 doesn't help (file is already parsed before it takes effect).

Usage: python generate_bats.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write_gbk(path: Path, content: str):
    path.write_text(content, encoding="gbk", errors="replace")
    non_ascii = sum(1 for c in content if ord(c) > 127)
    print(f"  {path.name}: written in GBK ({non_ascii} Chinese chars)")


SETUP_BAT = r"""@echo off
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
"""

START_BAT = r"""@echo off
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
"""

DIAGNOSE_BAT = r"""@echo off
setlocal enabledelayedexpansion

echo.
echo  ==========================================
echo    XHS Toolbox - Diagnostics
echo  ==========================================
echo.

set PASS=0
set FAIL=0

:: -- 1. Python --
echo  [1/6] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo    [FAIL] Python not installed
    echo    - Download: https://www.python.org/downloads/
    echo    - IMPORTANT: Check "Add Python to PATH" during install!
    set /a FAIL+=1
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo    [OK] %%v
    set /a PASS+=1
)
echo.

:: -- 2. Node.js --
echo  [2/6] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo    [WARN] Node.js not installed (search/hot features unavailable)
    echo    - Download: https://nodejs.org/  Choose LTS version
    set /a FAIL+=1
) else (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo    [OK] Node %%v
    set /a PASS+=1
)
echo.

:: -- 3. Python deps --
echo  [3/6] Checking Python packages...
set DEP_OK=1
for %%p in (flask requests jieba openpyxl loguru retry execjs dotenv) do (
    python -c "import %%p" >nul 2>&1
    if !errorlevel! neq 0 (
        echo    [FAIL] Missing: %%p
        set DEP_OK=0
    )
)
if %DEP_OK% equ 1 (
    echo    [OK] All Python packages installed
    set /a PASS+=1
) else (
    echo    - Run setup.bat to install dependencies
    set /a FAIL+=1
)
echo.

:: -- 4. .env config --
echo  [4/6] Checking config file...
if not exist .env (
    echo    [FAIL] .env file not found
    echo    - Run setup.bat to create it
    set /a FAIL+=1
) else (
    findstr /C:"your_cookie_here" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo    [WARN] Cookie not configured (features unavailable)
        echo    - Edit .env and fill in your XHS Cookie
        set /a FAIL+=1
    ) else (
        echo    [OK] Cookie configured
        set /a PASS+=1
    )
)
echo.

:: -- 5. Port --
echo  [5/6] Checking port 5001...
netstat -ano | findstr ":5001.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [WARN] Port 5001 already in use
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5001.*LISTENING"') do (
        echo    - Process PID: %%p
    )
    echo    - Close the program or change port
    set /a FAIL+=1
) else (
    echo    [OK] Port 5001 available
    set /a PASS+=1
)
echo.

:: -- 6. Project structure --
echo  [6/6] Checking project structure...
set DIR_OK=1
if not exist "工具类\博主蒸馏\spider_xhs" (
    echo    [FAIL] Missing spider_xhs directory
    set DIR_OK=0
)
if not exist "templates\index.html" (
    echo    [FAIL] Missing templates directory
    set DIR_OK=0
)
if not exist "requirements.txt" (
    echo    [FAIL] Missing requirements.txt
    set DIR_OK=0
)
if %DIR_OK% equ 1 (
    echo    [OK] Project structure complete
    set /a PASS+=1
) else (
    echo    - Re-extract the toolbox ZIP
    set /a FAIL+=1
)
echo.

:: -- Summary --
echo  ==========================================
echo    Result: %PASS% passed, %FAIL% issues
echo  ==========================================
echo.
if %FAIL% equ 0 (
    echo    All good! Double-click start.bat to launch
) else (
    echo    Please fix the issues above and try again
)
echo.
pause
"""


def main():
    print("Generating GBK-encoded .bat files...")
    write_gbk(ROOT / "setup.bat", SETUP_BAT)
    write_gbk(ROOT / "start.bat", START_BAT)
    write_gbk(ROOT / "diagnose.bat", DIAGNOSE_BAT)
    print("\nDone! All .bat files are now GBK-encoded.")


if __name__ == "__main__":
    main()
