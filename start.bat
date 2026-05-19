@echo off
chcp 65001 >/dev/null
echo ============================================
echo   小红书工具箱 - 启动
echo ============================================
echo.

:: 检查 .env
if not exist .env (
    if exist .env.example (
        echo ⚠️ 首次使用请先配置 .env 文件
        echo   将 .env.example 重命名为 .env
        echo   填入小红书 Cookie 和 DeepSeek API Key
        echo.
        pause
        exit /b 1
    )
)

echo 启动服务...
python app.py

if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查依赖和配置
    pause
)
