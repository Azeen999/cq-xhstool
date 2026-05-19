@echo off
chcp 65001 >nul
echo ============================================
echo   XHS Toolbox - Setup
echo ============================================
echo.

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo pip install failed, retrying without mirror...
    pip install -r requirements.txt
)
echo.

echo [2/3] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Node.js not found. Install from https://nodejs.org/
    echo   Skip npm install
) else (
    echo Node.js found
    echo [3/3] Installing Spider_XHS dependencies...
    cd 工具类\博主蒸馏\spider_xhs
    npm install
    cd ..\..\..
)
echo.

echo ============================================
echo Setup complete!
echo.
echo Next steps:
echo   1. Copy .env.example to .env
echo   2. Fill in Xiaohongshu Cookie and DeepSeek API Key
echo   3. Run start.bat
echo ============================================
pause
