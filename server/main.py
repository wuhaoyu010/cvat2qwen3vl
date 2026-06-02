"""
FastAPI 服务端
==============
提供 REST API + WebSocket，同时 serve Vue 静态文件。

启动:
    cd cvat2qwen3vl
    python -m server.main [preferred_port]
"""

import re
import socket
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api import router as api_router
from .ws import handle_pipeline_ws

PROJECT_ROOT = Path(__file__).parent.parent
PORT_FILE = PROJECT_ROOT / ".backend_port"

app = FastAPI(title="cvat2qwen3vl", version="1.0.0")

# CORS (开发模式: Vite dev server 在 5173 端口)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[re.compile(r"^http://localhost:\d+$"), re.compile(r"^http://127\.0\.0\.1:\d+$")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================

app.include_router(api_router)


# ==================== WebSocket ====================

@app.websocket("/ws/pipeline")
async def pipeline_ws(websocket: WebSocket):
    await handle_pipeline_ws(websocket)


# ==================== Serve Vue 静态文件 ====================

DIST_DIR = Path(__file__).parent.parent / "web" / "dist"

if DIST_DIR.exists():
    # 挂载 assets 目录
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_vue(full_path: str):
        """Vue SPA fallback: 所有未匹配的路由都返回 index.html"""
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "message": "cvat2qwen3vl API running",
            "docs": "/docs",
            "note": "Vue 前端未构建, 请运行: cd web && npm run build",
        }


# ==================== 端口自动检测 ====================

def find_available_port(preferred: int) -> int:
    """尝试绑定端口，冲突时自动 +1 重试"""
    for port in range(preferred, preferred + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found in range {preferred}-{preferred+99}")


def write_port_file(port: int):
    """将实际端口写入 .backend_port"""
    PORT_FILE.write_text(str(port))


def main():
    import uvicorn

    preferred = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    port = find_available_port(preferred)
    write_port_file(port)

    if port != preferred:
        print(f"Port {preferred} in use, switched to {port}")

    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
