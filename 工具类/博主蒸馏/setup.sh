#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  📦 博主蒸馏器 — 环境自动安装"
echo "============================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# -------- 1. Check Python --------
echo -e "[1/4] 检查 Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}❌ 未找到 Python！请先安装 Python 3.10+${NC}"
    exit 1
fi
$PYTHON --version
echo -e "${GREEN}✅ Python 已安装${NC}"
echo ""

# -------- 2. Check Node.js --------
echo -e "[2/4] 检查 Node.js..."
if command -v node &> /dev/null; then
    node --version
    echo -e "${GREEN}✅ Node.js 已安装${NC}"
else
    echo -e "${YELLOW}⚠️ 未找到 Node.js！Spider_XHS 需要 Node.js 生成签名。${NC}"
    echo "   安装: https://nodejs.org/"
fi
echo ""

# -------- 3. Install Spider_XHS Node.js deps --------
echo -e "[3/4] 安装 Spider_XHS 依赖..."
if [ -f "spider_xhs/package.json" ]; then
    cd spider_xhs
    npm install --production 2>&1 || echo -e "${YELLOW}⚠️ npm install 有警告${NC}"
    cd ..
    echo -e "${GREEN}✅ Spider_XHS 依赖已安装${NC}"
else
    echo -e "${YELLOW}⚠️ 未找到 spider_xhs/package.json，跳过${NC}"
fi
echo ""

# -------- 4. Install Python deps --------
echo -e "[4/4] 安装 Python 包..."
$PYTHON -m pip install -r requirements.txt
echo -e "${GREEN}✅ Python 依赖已安装${NC}"
echo ""

# -------- Done --------
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "下一步：配置小红书 Cookie"
echo ""
echo "  1. 登录 https://www.xiaohongshu.com"
echo "  2. 打开开发者工具 → Network"
echo "  3. 刷新页面，复制 Cookie 值"
echo "  4. 编辑 spider_xhs/.env，写入："
echo "     COOKIES=你的完整Cookie值"
echo ""
echo "启动方式："
echo "  python3 app.py          — 打开 Web 界面"
echo "  python3 run.py \"博主名\" — 命令行运行"
echo ""
