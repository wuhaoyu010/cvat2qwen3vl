"""
模型注册表
==========
集中管理所有支持的 Qwen-VL 系列模型元数据。

为何需要这个文件:
    1. 不同模型版本可能有不同的归一化范围 (例如 Qwen2-VL 早期版本是 0-256)
    2. 不同模型有不同的 patch_size (Qwen2.5-VL=14, Qwen3-VL+=16), 影响训练配置
    3. 未来新增模型只需在此添加条目, 无需改动其他代码

归一化范围说明:
    - Qwen2-VL 旧版本: 0-256 (已废弃, 现统一为 0-1000)
    - Qwen2.5-VL: 0-1000
    - Qwen3-VL 系列: 0-1000
    - Qwen3.5-VL 系列: 0-1000
    - Qwen3.6-VL 系列: 0-1000

数据预处理格式说明 (所有 Qwen2.5-VL+ 模型统一):
    ms-swift 格式:
        {"messages": [...], "images": [...], "objects": {"ref": [...], "bbox": [...]}}
    Unsloth 格式:
        {"messages": [{"role":"user","content":[...]}, {"role":"assistant","content":[...]}]}
        其中 bbox 已归一化到 0-1000
"""

from typing import Dict, List, Optional


# ======================== 模型元数据 ========================

MODELS: Dict[str, Dict] = {
    # ----- Qwen2.5-VL -----
    "Qwen2.5-VL-3B-Instruct": {
        "family": "qwen2.5-vl",
        "hf_id": "Qwen/Qwen2.5-VL-3B-Instruct",
        "patch_size": 14,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen2.5-VL 3B 模型, 适合入门和轻量场景",
    },
    "Qwen2.5-VL-7B-Instruct": {
        "family": "qwen2.5-vl",
        "hf_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "patch_size": 14,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen2.5-VL 7B 模型, 性能与资源平衡",
    },
    "Qwen2.5-VL-32B-Instruct": {
        "family": "qwen2.5-vl",
        "hf_id": "Qwen/Qwen2.5-VL-32B-Instruct",
        "patch_size": 14,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen2.5-VL 32B 模型, 高精度 (需多卡)",
    },
    "Qwen2.5-VL-72B-Instruct": {
        "family": "qwen2.5-vl",
        "hf_id": "Qwen/Qwen2.5-VL-72B-Instruct",
        "patch_size": 14,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen2.5-VL 72B 模型, 顶级性能",
    },

    # ----- Qwen3-VL (Instruct/Thinking 系列) -----
    "Qwen3-VL-2B-Instruct": {
        "family": "qwen3-vl",
        "hf_id": "Qwen/Qwen3-VL-2B-Instruct",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3-VL 2B 轻量级, 推荐入门",
    },
    "Qwen3-VL-4B-Instruct": {
        "family": "qwen3-vl",
        "hf_id": "Qwen/Qwen3-VL-4B-Instruct",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3-VL 4B 平衡版",
    },
    "Qwen3-VL-8B-Instruct": {
        "family": "qwen3-vl",
        "hf_id": "Qwen/Qwen3-VL-8B-Instruct",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3-VL 8B 主力模型, 推荐",
    },
    "Qwen3-VL-32B-Instruct": {
        "family": "qwen3-vl",
        "hf_id": "Qwen/Qwen3-VL-32B-Instruct",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3-VL 32B 高精度 (需多卡)",
    },
    "Qwen3-VL-30B-A3B-Instruct": {
        "family": "qwen3-vl",
        "hf_id": "Qwen/Qwen3-VL-30B-A3B-Instruct",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3-VL 30B MoE, A3B激活参数",
    },
    "Qwen3-VL-235B-A22B-Instruct": {
        "family": "qwen3-vl",
        "hf_id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3-VL 235B MoE, 顶级",
    },

    # ----- Qwen3.5-VL -----
    "Qwen3.5-VL-2B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-2B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 2B, 轻量级",
    },
    "Qwen3.5-VL-4B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-4B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 4B",
    },
    "Qwen3.5-VL-9B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-9B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 9B",
    },
    "Qwen3.5-VL-27B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-27B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 27B, 主力模型",
    },
    "Qwen3.5-VL-35B-A3B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-35B-A3B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 35B MoE",
    },
    "Qwen3.5-VL-122B-A10B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-122B-A10B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 122B MoE",
    },
    "Qwen3.5-VL-397B-A17B": {
        "family": "qwen3.5-vl",
        "hf_id": "Qwen/Qwen3.5-VL-397B-A17B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.5-VL 397B MoE, 旗舰级",
    },

    # ----- Qwen3.6-VL -----
    "Qwen3.6-VL-27B": {
        "family": "qwen3.6-vl",
        "hf_id": "Qwen/Qwen3.6-VL-27B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.6-VL 27B, 最新版本",
    },
    "Qwen3.6-VL-35B-A3B": {
        "family": "qwen3.6-vl",
        "hf_id": "Qwen/Qwen3.6-VL-35B-A3B",
        "patch_size": 16,
        "coord_range": 1000,
        "image_token": "<image>",
        "description": "Qwen3.6-VL 35B MoE, 最新版本",
    },
}


# ======================== 工具函数 ========================

def list_models() -> List[Dict]:
    """列出所有支持的模型 (按家族分组)"""
    result = []
    for name, meta in MODELS.items():
        result.append({
            "name": name,
            "family": meta["family"],
            "hf_id": meta["hf_id"],
            "patch_size": meta["patch_size"],
            "coord_range": meta["coord_range"],
            "description": meta["description"],
        })
    return result


def get_model(name_or_path: str) -> Optional[Dict]:
    """
    根据名称或路径查找模型元数据。

    支持:
        - 简称: "Qwen3-VL-8B-Instruct"
        - HF ID: "Qwen/Qwen3-VL-8B-Instruct"
        - 本地路径: "/path/to/model"
    """
    if name_or_path in MODELS:
        return {"name": name_or_path, **MODELS[name_or_path]}

    # 通过 hf_id 查找
    for name, meta in MODELS.items():
        if meta["hf_id"] == name_or_path:
            return {"name": name, **meta}

    # 本地路径或未知模型, 返回默认值 (按 Qwen3-VL 系列)
    if "/" in name_or_path or "\\" in name_or_path or name_or_path.startswith("."):
        return {
            "name": name_or_path,
            "family": "custom",
            "hf_id": name_or_path,
            "patch_size": 16,
            "coord_range": 1000,
            "image_token": "<image>",
            "description": "本地或自定义模型, 默认按Qwen3-VL参数处理",
        }

    return None


def get_coord_range(name_or_path: str) -> int:
    """获取模型使用的坐标归一化范围 (默认1000)"""
    meta = get_model(name_or_path)
    if meta:
        return meta["coord_range"]
    return 1000


def get_default_model() -> str:
    """默认推荐模型"""
    return "Qwen3-VL-8B-Instruct"


def get_grouped_models() -> Dict[str, List[str]]:
    """按家族分组返回模型列表 (用于前端下拉)"""
    grouped = {}
    for name, meta in MODELS.items():
        family = meta["family"]
        if family not in grouped:
            grouped[family] = []
        grouped[family].append(name)
    return grouped
