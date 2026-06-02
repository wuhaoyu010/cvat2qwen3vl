"""
坐标转换工具
=============
处理CVAT绝对像素坐标 → Qwen-VL系列目标格式的转换:

1. polygon/polyline/points → axis-aligned bounding box (外接矩形)
2. OBB (旋转框) → axis-aligned bounding box
3. 绝对像素坐标 → 归一化0-RANGE坐标 (仅Unsloth路径需要)

坐标约定:
  - CVAT:           绝对像素 [xtl, ytl, xbr, ybr]
  - Qwen-VL 标准:   归一化0-1000 [x1, y1, x2, y2]
  - ms-swift:       传绝对坐标, 框架自动转换到0-1000
  - Unsloth:        必须手动归一化到模型对应的范围 (默认1000)

支持的归一化范围 (通过 model_registry 配置):
  - 1000: Qwen2.5-VL / Qwen3-VL / Qwen3.5-VL / Qwen3.6-VL 默认
  - 256:  Qwen2-VL 早期版本 (已废弃, 保留兼容性)
"""

import math
from typing import List, Tuple, Optional

from model_registry import get_coord_range


def polygon_to_bbox(points: List[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
    """
    多边形/折线/关键点 → axis-aligned bounding box
    
    原理: 取所有点的 min(x), min(y), max(x), max(y)
    
    参数:
        points: [(x0, y0), (x1, y1), ...] 点序列
        
    返回:
        (xmin, ymin, xmax, ymax) 或 None (空点集)
        
    示例:
        >>> polygon_to_bbox([(100, 200), (300, 100), (500, 400)])
        (100, 100, 500, 400)
    """
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def obb_to_bbox(
    cx: float, cy: float, w: float, h: float, angle_deg: float
) -> Tuple[float, float, float, float]:
    """
    旋转框 (OBB) → axis-aligned bounding box
    
    原理:
        1. 根据中心(cx,cy)、宽高(w,h)、旋转角度(angle_deg)计算4个顶点
        2. 取4顶点的min/max得到外接矩形
    
    参数:
        cx, cy:     旋转框中心坐标 (绝对像素)
        w, h:       旋转框的宽高 (绝对像素)
        angle_deg:  旋转角度 (度, 逆时针为正)
        
    返回:
        (xmin, ymin, xmax, ymax)
        
    示例:
        >>> obb_to_bbox(100, 100, 60, 40, 45)
        (78.79, 64.64, 121.21, 135.36)  # 近似值
    """
    rad = math.radians(angle_deg)
    cos_a = abs(math.cos(rad))
    sin_a = abs(math.sin(rad))
    
    # 旋转后外接矩形的宽高
    new_w = w * cos_a + h * sin_a
    new_h = w * sin_a + h * cos_a
    
    return (cx - new_w / 2, cy - new_h / 2, cx + new_w / 2, cy + new_h / 2)


def normalize_bbox_to_1000(
    bbox: Tuple[float, float, float, float],
    img_w: int, img_h: int
) -> Tuple[int, int, int, int]:
    """
    绝对像素bbox → 归一化到0-1000坐标 (Qwen2.5-VL+ 默认)

    公式 (来源: Qwen3-VL官方GitHub Issue #1616):
        normalized = round(original / dimension * 1000)

    参数:
        bbox:   (xmin, ymin, xmax, ymax) 绝对像素坐标
        img_w:  图片宽度 (像素)
        img_h:  图片高度 (像素)

    返回:
        (x1, y1, x2, y2) 归一化到0-1000的整数坐标

    注意:
        此函数仅在使用 Unsloth 或原生transformers 时需要。
        使用 ms-swift 时无需手动调用 (框架自动处理)。

    示例:
        >>> normalize_bbox_to_1000((100, 200, 500, 400), 1920, 1080)
        (52, 185, 260, 370)
    """
    return normalize_bbox(bbox, img_w, img_h, coord_range=1000)


def normalize_bbox(
    bbox: Tuple[float, float, float, float],
    img_w: int, img_h: int,
    coord_range: int = 1000
) -> Tuple[int, int, int, int]:
    """
    绝对像素bbox → 归一化到0-coord_range坐标 (通用版本)

    公式:
        normalized = round(original / dimension * coord_range)

    参数:
        bbox:        (xmin, ymin, xmax, ymax) 绝对像素坐标
        img_w:       图片宽度 (像素)
        img_h:       图片高度 (像素)
        coord_range: 归一化目标范围 (默认1000, 历史曾用256)

    返回:
        (x1, y1, x2, y2) 归一化到0-coord_range的整数坐标
    """
    x1, y1, x2, y2 = bbox
    return (
        round(x1 / img_w * coord_range),
        round(y1 / img_h * coord_range),
        round(x2 / img_w * coord_range),
        round(y2 / img_h * coord_range)
    )


def normalize_bbox_for_model(
    bbox: Tuple[float, float, float, float],
    img_w: int, img_h: int,
    model_name: str
) -> Tuple[int, int, int, int]:
    """
    根据模型自动选择归一化范围

    参数:
        bbox:       (xmin, ymin, xmax, ymax) 绝对像素坐标
        img_w:      图片宽度
        img_h:      图片高度
        model_name: 模型名称或HF ID (如 "Qwen3-VL-8B-Instruct" 或 "Qwen/Qwen3-VL-8B-Instruct")

    返回:
        (x1, y1, x2, y2) 归一化到该模型对应的整数坐标
    """
    coord_range = get_coord_range(model_name)
    return normalize_bbox(bbox, img_w, img_h, coord_range)


def denormalize_bbox_from_1000(
    norm_bbox: Tuple[int, int, int, int],
    img_w: int, img_h: int
) -> Tuple[float, float, float, float]:
    """
    归一化0-1000坐标 → 绝对像素bbox (推理后处理用)

    公式:
        pixel = normalized / 1000 * (dimension - 1)

    参数:
        norm_bbox: (x1, y1, x2, y2) 归一化坐标
        img_w:     图片宽度
        img_h:     图片高度

    返回:
        (xmin, ymin, xmax, ymax) 绝对像素坐标
    """
    return denormalize_bbox(norm_bbox, img_w, img_h, coord_range=1000)


def denormalize_bbox(
    norm_bbox: Tuple[int, int, int, int],
    img_w: int, img_h: int,
    coord_range: int = 1000
) -> Tuple[float, float, float, float]:
    """
    归一化坐标 → 绝对像素bbox (通用版本)
    """
    x1, y1, x2, y2 = norm_bbox
    return (
        x1 / coord_range * (img_w - 1),
        y1 / coord_range * (img_h - 1),
        x2 / coord_range * (img_w - 1),
        y2 / coord_range * (img_h - 1)
    )


def annotation_to_bbox(annotation) -> Optional[Tuple[float, float, float, float]]:
    """
    将Annotation对象统一转换为axis-aligned bbox
    
    处理逻辑:
        - box:       直接返回 bbox
        - polygon:   计算外接矩形
        - polyline:  计算外接矩形
        - points:    计算外接矩形
        - skeleton:  计算所有关键点的外接矩形
        - tag/mask:  返回 None (无bbox信息)
    
    参数:
        annotation: Annotation对象 (来自cvat_parser)
        
    返回:
        (xmin, ymin, xmax, ymax) 或 None
    """
    if annotation.shape_type == 'box' and annotation.bbox is not None:
        return annotation.bbox
    
    if annotation.polygon_points and len(annotation.polygon_points) >= 2:
        return polygon_to_bbox(annotation.polygon_points)
    
    return None
