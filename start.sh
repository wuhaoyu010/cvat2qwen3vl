#!/usr/bin/env bash
# ============================================
#  cvat2qwen3vl 一键启动 (开发模式)
#  用法: chmod +x start.sh && ./start.sh
# ============================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREFERRED_PORT=8001
FRONTEND_PORT=5173

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    rm -f "$PROJECT_DIR/.backend_port"
    echo -e "${GREEN}已停止所有服务${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}============================================"
echo -e "  cvat2qwen3vl 开发模式"
echo -e "============================================${NC}"
echo ""

# 检查 Python 虚拟环境
if [ ! -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    echo -e "${RED}[错误] 未找到 Python 虚拟环境 .venv${NC}"
    echo "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 配置 pnpm 阿里镜像源
pnpm config set registry https://registry.npmmirror.com 2>/dev/null || true
export npm_config_registry=https://registry.npmmirror.com

# 检查 node_modules
if [ ! -d "$PROJECT_DIR/web/node_modules" ]; then
    echo -e "${YELLOW}[提示] 正在安装前端依赖...${NC}"
    cd "$PROJECT_DIR/web"
    pnpm install --fetch-timeout 120000
fi

# 激活虚拟环境
source "$PROJECT_DIR/.venv/bin/activate"

# 清理旧的端口文件
rm -f "$PROJECT_DIR/.backend_port"

echo -e "${GREEN}[1/2] 启动后端 (自动检测端口)...${NC}"

# 启动后端 (后台)
cd "$PROJECT_DIR"
python -m server.main $PREFERRED_PORT &
BACKEND_PID=$!

# 等待 .backend_port 文件出现
WAIT=0
while [ ! -f "$PROJECT_DIR/.backend_port" ] && [ $WAIT -lt 10 ]; do
    sleep 0.2
    WAIT=$((WAIT + 1))
done

if [ ! -f "$PROJECT_DIR/.backend_port" ]; then
    echo -e "${RED}[错误] 后端启动超时${NC}"
    cleanup
    exit 1
fi

BACKEND_PORT=$(cat "$PROJECT_DIR/.backend_port")

echo -e "${GREEN}[2/2] 启动前端 (port $FRONTEND_PORT)...${NC}"
echo ""
echo -e "  后端: ${CYAN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  前端: ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止所有服务"
echo -e "────────────────────────────────────────────"

# 启动前端 (前台)
cd "$PROJECT_DIR/web"
pnpm dev

# 前端退出时清理
cleanup
