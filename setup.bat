@echo off
chcp 65001 >/dev/null
echo ============================================
echo   小红书工具箱 - 一键安装
echo ============================================
echo.

echo [1/3] 安装 Python 依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo pip 安装失败，尝试无镜像源...
    pip install -r requirements.txt
)
echo.

echo [2/3] 检查 Node.js...
where node >/dev/null 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 未检测到 Node.js，请先安装 https://nodejs.org/
    echo   部分小红书API加密功能需要 Node.js 运行环境
    echo   跳过 npm install
) else (
    echo Node.js 已安装
    echo [3/3] 安装 Spider_XHS 依赖...
    cd 工具类\博主蒸馏\spider_xhs
    npm install
    cd ..\..\..
)
echo.

echo ============================================
echo ✅ 安装完成！
echo.
echo 接下来需要配置 Cookie：
echo   1. 复制 .env.example 为 .env
echo   2. 填入小红书 Cookie 和 DeepSeek API Key
echo   3. 运行 start.bat 启动
echo ============================================
pause
