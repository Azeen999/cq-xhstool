@echo off
chcp 65001 >nul
echo ============================================
echo   XHS Toolbox - Starting...
echo ============================================
echo.

if not exist .env (
    if exist .env.example (
        echo [INFO] First time setup required.
        echo   Copy .env.example to .env
        echo   Fill in your Xiaohongshu Cookie and DeepSeek API Key
        echo.
        pause
        exit /b 1
    )
)

echo Starting server...
python app.py

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start. Check dependencies and configuration.
    pause
)
