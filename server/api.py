"""
REST API 路由
=============
提供文件上传、下载、配置读取、训练启动、模型管理、路径历史等接口。
"""

import json
import shutil
import subprocess
import sys
import shutil as _shutil
from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from model_registry import list_models, get_grouped_models, get_model, get_default_model

router = APIRouter(prefix="/api")

PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "output"
TRAINING_LOG = PROJECT_ROOT / "training.log"
UPLOAD_DIR.mkdir(exist_ok=True)

# 模型路径历史文件 (用户家目录下)
HISTORY_FILE = Path.home() / ".cvat2qwen3vl" / "model_history.json"
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

MAX_HISTORY = 20


# ======================== 模型管理 ========================

@router.get("/models")
async def get_models():
    """
    返回所有支持的模型列表 (按家族分组) + 历史路径。
    前端用此填充下拉框。
    """
    return {
        "grouped": get_grouped_models(),
        "flat": list_models(),
        "default": get_default_model(),
    }


@router.get("/models/{model_name:path}")
async def get_model_info(model_name: str):
    """查询单个模型的元数据 (支持简称/HF ID/本地路径)"""
    meta = get_model(model_name)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"未找到模型: {model_name}")
    return meta


class PathHistoryRequest(BaseModel):
    path: str
    note: Optional[str] = None


@router.get("/model-history")
async def get_model_history():
    """获取用户用过的模型路径历史 (最近 MAX_HISTORY 条)"""
    if not HISTORY_FILE.exists():
        return {"history": []}
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {"history": data if isinstance(data, list) else []}
    except Exception:
        return {"history": []}


@router.post("/model-history")
async def add_model_history(req: PathHistoryRequest):
    """
    记录一条模型路径到历史。
    重复路径移到最前, 最多保留 MAX_HISTORY 条。
    """
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []

    # 去重
    history = [h for h in history if h.get("path") != req.path]
    # 插入新条目
    history.insert(0, {
        "path": req.path,
        "note": req.note or "",
        "timestamp": int(__import__("time").time()),
    })
    # 截断
    history = history[:MAX_HISTORY]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return {"history": history}


@router.delete("/model-history")
async def clear_model_history():
    """清空历史"""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    return {"status": "cleared"}


# ======================== 文件上传/下载 ========================

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    上传 ZIP 文件到服务器 (支持多文件批量上传)。
    返回保存后的绝对路径列表，供 pipeline 使用。
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    for f in files:
        # 安全: 仅保留文件名, 去掉路径
        safe_name = Path(f.filename).name
        save_path = UPLOAD_DIR / safe_name
        with open(save_path, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved_paths.append(str(save_path.resolve()))
    return {"paths": saved_paths, "count": len(saved_paths)}


@router.get("/download")
async def download_file(path: str):
    """下载生成的训练文件"""
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(p, filename=p.name, media_type="application/octet-stream")


# ======================== 配置 ========================

@router.get("/config")
async def get_config():
    """读取当前 config.yaml 配置"""
    config_path = PROJECT_ROOT / "config.yaml"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


# ======================== 输出文件列表 ========================

@router.get("/output-files")
async def list_output_files():
    """列出已生成的输出文件 (按 framework/family 目录结构)"""
    files = {}
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return files

    for framework_dir in OUTPUT_DIR.iterdir():
        if not framework_dir.is_dir():
            continue
        framework = framework_dir.name
        # 支持嵌套目录 (framework/family/file)
        for f in framework_dir.rglob("*"):
            if f.is_file() and f.suffix in (".jsonl", ".json", ".yaml", ".txt"):
                rel = f.relative_to(framework_dir)
                key = f"{framework}/{rel.as_posix()}"
                files[key] = {
                    "path": str(f.resolve()),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "framework": framework,
                    "subpath": rel.parent.as_posix() if rel.parent != Path(".") else "",
                }
    return files


# ======================== 训练启动 ========================

def _check_swift_available() -> bool:
    """检查 swift 命令是否可用"""
    return _shutil.which("swift") is not None


@router.get("/training-log")
async def get_training_log(lines: int = 200):
    """读取训练日志 (最后 N 行)"""
    if not TRAINING_LOG.exists():
        return {"log": "", "exists": False}
    try:
        content = TRAINING_LOG.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()
        return {"log": "\n".join(all_lines[-lines:]), "exists": True, "total_lines": len(all_lines)}
    except Exception as e:
        return {"log": f"Error reading log: {e}", "exists": False}


@router.post("/launch-training")
async def launch_training(params: dict):
    """
    启动训练脚本 (非阻塞, 返回task_id)。
    """
    framework = params.get("framework", "swift")
    model_path = params.get("model_path") or get_default_model()
    epochs = params.get("epochs", 3)
    batch_size = params.get("batch_size", 2)
    lr = params.get("lr", 1e-4)
    lora_rank = params.get("lora_rank", 16)
    model_family = params.get("model_family") or ""

    # ms-swift 可用性检查
    if framework == "swift" and not _check_swift_available():
        raise HTTPException(
            status_code=400,
            detail=(
                "ms-swift 未安装。请先执行: pip install ms-swift\n"
                "或在服务器上运行: pip install 'ms-swift[all]'"
            ),
        )

    # 记录到历史
    try:
        req = PathHistoryRequest(path=model_path, note=f"{framework} - {model_family}")
        await add_model_history(req)
    except Exception:
        pass

    # 解析训练数据路径 (按 framework/family 子目录)
    if model_family:
        train_file = OUTPUT_DIR / framework / model_family / (
            "train.jsonl" if framework == "swift" else "train.json"
        )
    else:
        train_file = OUTPUT_DIR / framework / (
            "train.jsonl" if framework == "swift" else "train.json"
        )

    if not train_file.exists():
        # 兜底: 找 framework 下任意 train 文件
        candidates = list((OUTPUT_DIR / framework).rglob("train.*")) if (OUTPUT_DIR / framework).exists() else []
        if not candidates:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"训练数据不存在: {train_file}。"
                    f"请先运行数据处理pipeline, 并选择正确的模型家族。"
                ),
            )
        train_file = candidates[0]

    if framework == "swift":
        cmd = [
            "swift", "sft",
            "--model", model_path,
            "--dataset", str(train_file),
            "--output_dir", str(OUTPUT_DIR / framework / "checkpoints"),
            "--tuner_type", "lora",
            "--lora_rank", str(lora_rank),
            "--target_modules", "all-linear",
            "--freeze_vit", "true",
            "--freeze_aligner", "true",
            "--packing", "true",
            "--num_train_epochs", str(epochs),
            "--per_device_train_batch_size", str(batch_size),
            "--learning_rate", str(lr),
            "--torch_dtype", "bfloat16",
            "--attn_impl", "flash_attn",
            "--logging_steps", "10",
        ]
    else:
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "train_unsloth.py"),
            "--model_name", model_path,
            "--train_file", str(train_file),
        ]

    try:
        # 输出重定向到日志文件
        log_fh = open(TRAINING_LOG, "w", encoding="utf-8")
        process = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        return {
            "status": "started",
            "pid": process.pid,
            "command": " ".join(cmd),
            "train_file": str(train_file),
            "model_path": model_path,
            "log_file": str(TRAINING_LOG),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动训练失败: {e}")
