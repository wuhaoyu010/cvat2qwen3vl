#!/usr/bin/env bash
# ============================================
#  cvat2qwen3vl 一键启动 (生产模式)
#  用法: chmod +x start-prod.sh && ./start-prod.sh
# ============================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREFERRED_PORT=8001

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    rm -f "$PROJECT_DIR/.backend_port"
    echo -e "${GREEN}已停止服务${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}============================================"
echo -e "  cvat2qwen3vl 生产模式"
echo -e "============================================${NC}"
echo ""

# 检查 Python 虚拟环境
if [ ! -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    echo -e "${RED}[错误] 未找到 Python 虚拟环境 .venv${NC}"
    exit 1
fi

# 激活虚拟环境
source "$PROJECT_DIR/.venv/bin/activate"

# 构建前端 (如果 dist 不存在)
if [ ! -f "$PROJECT_DIR/web/dist/index.html" ]; then
    echo -e "${GREEN}[1/2] 构建前端...${NC}"
    pnpm config set registry https://registry.npmmirror.com 2>/dev/null || true
    export npm_config_registry=https://registry.npmmirror.com
    cd "$PROJECT_DIR/web"
    pnpm build --network-timeout 300000 --fetch-timeout 120000
    echo ""
else
    echo -e "${YELLOW}[提示] 前端已构建，跳过 (如需重新构建请删除 web/dist)${NC}"
    echo ""
fi

# 清理旧的端口文件
rm -f "$PROJECT_DIR/.backend_port"

echo -e "${GREEN}[2/2] 启动服务 (自动检测端口)...${NC}"

cd "$PROJECT_DIR"
python -m server.main $PREFERRED_PORT &
SERVER_PID=$!

# 等待 .backend_port 文件出现
WAIT=0
while [ ! -f "$PROJECT_DIR/.backend_port" ] && [ $WAIT -lt 10 ]; do
    sleep 0.2
    WAIT=$((WAIT + 1))
done

if [ ! -f "$PROJECT_DIR/.backend_port" ]; then
    echo -e "${RED}[错误] 服务启动超时${NC}"
    cleanup
    exit 1
fi

PORT=$(cat "$PROJECT_DIR/.backend_port")

echo ""
echo -e "  访问:       ${CYAN}http://localhost:$PORT${NC}"
echo -e "  API 文档:   ${CYAN}http://localhost:$PORT/docs${NC}"
echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止"
echo -e "────────────────────────────────────────────"

wait $SERVER_PID
