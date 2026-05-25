@echo off
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
