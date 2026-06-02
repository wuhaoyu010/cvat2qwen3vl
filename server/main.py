"""
FastAPI 服务端
===============
提供 REST API + WebSocket，同时 serve Vue 静态文件。

启动:
    cd cvat2qwen3vl
    uvicorn server.main:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api import router as api_router
from .ws import handle_pipeline_ws

app = FastAPI(title="cvat2qwen3vl", version="1.0.0")

# CORS (开发模式: Vite dev server 在 5173 端口)
import re
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
