"""
图片工具函数
=============
提供图片信息读取、验证等功能。
"""

from pathlib import Path
from typing import Optional, Tuple


def get_image_info(image_path: str) -> Optional[Tuple[int, int]]:
    """
    获取图片尺寸 (宽, 高)
    
    参数:
        image_path: 图片文件路径
        
    返回:
        (width, height) 或 None (读取失败)
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception:
        return None


def validate_image(image_path: str) -> bool:
    """
    验证图片文件是否可正常读取
    
    参数:
        image_path: 图片文件路径
        
    返回:
        True 如果图片可读, False 否则
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def get_image_format(image_path: str) -> Optional[str]:
    """
    获取图片格式 (jpg, png, etc.)
    
    参数:
        image_path: 图片文件路径
        
    返回:
        格式字符串 (小写) 或 None
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            fmt = img.format
            return fmt.lower() if fmt else None
    except Exception:
        return None
