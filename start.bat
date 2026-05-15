@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   小红书工具箱 — 启动中...
echo   打开浏览器访问 http://localhost:5001
echo   关闭此窗口 = 停止服务
echo ================================================
python app.py
pause
