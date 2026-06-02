#!/usr/bin/env bash
# ============================================
#  cvat2qwen3vl 首次安装 (Linux / macOS)
#  用法: chmod +x setup.sh && ./setup.sh
# ============================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================"
echo -e "  cvat2qwen3vl 首次安装"
echo -e "============================================${NC}"
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[错误] 未找到 Python3，请先安装${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "  macOS: brew install python3"
    exit 1
fi

# 检查 Node.js
if ! command -v node &>/dev/null; then
    echo -e "${RED}[错误] 未找到 Node.js，请先安装 18+${NC}"
    echo "  下载: https://nodejs.org/"
    exit 1
fi

# 检查 pnpm
if ! command -v pnpm &>/dev/null; then
    echo -e "${YELLOW}[提示] 正在安装 pnpm...${NC}"
    npm install -g pnpm --registry https://registry.npmmirror.com
fi

# 配置 pnpm 阿里镜像源 + 超时
echo -e "${YELLOW}[提示] 配置 pnpm 阿里镜像源...${NC}"
pnpm config set registry https://registry.npmmirror.com 2>/dev/null || true
export npm_config_registry=https://registry.npmmirror.com
export npm_config_fetch_timeout=120000
export npm_config_fetch_retry_mintimeout=60000
export npm_config_fetch_retry_maxtimeout=300000

# 创建虚拟环境
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo -e "${GREEN}[1/3] 创建 Python 虚拟环境...${NC}"
    cd "$PROJECT_DIR"
    python3 -m venv .venv
fi

# 激活虚拟环境
source "$PROJECT_DIR/.venv/bin/activate"

# 安装 Python 依赖
echo -e "${GREEN}[2/3] 安装 Python 依赖...${NC}"
cd "$PROJECT_DIR"
pip install -r requirements.txt
pip install fastapi "uvicorn[standard]" python-multipart websockets

# 安装前端依赖
echo -e "${GREEN}[3/3] 安装前端依赖...${NC}"
cd "$PROJECT_DIR/web"
pnpm install  --fetch-timeout 120000

echo ""
echo -e "${CYAN}============================================"
echo -e "  安装完成!"
echo -e "============================================${NC}"
echo ""
echo -e "  启动开发模式: ${GREEN}./start.sh${NC}"
echo -e "  启动生产模式: ${GREEN}./start-prod.sh${NC}"
