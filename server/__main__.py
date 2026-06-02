"""
FastAPI 服务端
==============
提供 REST API + WebSocket，同时 serve Vue 静态文件。

启动:
    cd cvat2qwen3vl
    python -m server.main
"""

import socket
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PORT_FILE = PROJECT_ROOT / ".backend_port"


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
