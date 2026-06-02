"""
WebSocket 进度推送
==================
每个客户端连接创建独立 handler，通过 pipeline_runner 生成进度事件并推送。
"""

import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from .pipeline_runner import run_pipeline_ws


class ConnectionManager:
    """管理 WebSocket 连接"""

    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        conn_id = str(uuid.uuid4())[:8]
        self.active[conn_id] = ws
        return conn_id

    def disconnect(self, conn_id: str):
        self.active.pop(conn_id, None)


manager = ConnectionManager()


async def handle_pipeline_ws(ws: WebSocket):
    """
    处理一个 pipeline WebSocket 连接。

    客户端发送:
        {"type": "start", "input_paths": [...], "output_dir": "...", "config": {...}}

    服务端推送:
        {"type": "progress", "step": "...", "progress": 0.0~1.0}
        {"type": "log",      "message": "..."}
        {"type": "result",   "data": {...}}
        {"type": "error",    "message": "..."}
    """
    conn_id = await manager.connect(ws)
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "start":
                input_paths = msg.get("input_paths", [])
                output_dir = msg.get("output_dir", "./output")
                config = msg.get("config", {})

                if not input_paths:
                    await ws.send_text(json.dumps({
                        "type": "error",
                        "message": "未提供输入文件路径",
                    }))
                    continue

                # 通过 pipeline_runner 生成事件并逐条推送
                async for event in run_pipeline_ws(input_paths, output_dir, config):
                    await ws.send_text(json.dumps(event, ensure_ascii=False))

            elif msg.get("type") == "cancel":
                await ws.send_text(json.dumps({
                    "type": "log",
                    "message": "取消功能暂未实现",
                }))

    except WebSocketDisconnect:
        manager.disconnect(conn_id)
    except Exception as e:
        try:
            await ws.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except Exception:
            pass
        manager.disconnect(conn_id)
