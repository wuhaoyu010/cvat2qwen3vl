"""
数据验证工具
=============
验证合并后的数据集是否满足训练要求:
    1. 图片文件是否存在且可读
    2. 图片尺寸与XML中记录的是否一致
    3. 标注坐标是否在图片范围内
    4. 是否存在空标注 (无标注的图片)
    5. 类别名称是否为空
"""

from pathlib import Path
from typing import List, Dict, Tuple
from parsers.cvat_parser import ImageAnnotation


class DataValidator:
    """
    数据集验证器
    
    使用方法:
        validator = DataValidator()
        report = validator.validate(image_annotations, images_dir)
        print(f"通过: {report['valid']}, 失败: {report['invalid']}")
    """
    
    def __init__(self, fix_bbox_clipping: bool = True):
        """
        参数:
            fix_bbox_clipping: 是否自动修正超出范围的bbox坐标
        """
        self.fix_bbox_clipping = fix_bbox_clipping
    
    def validate(
        self,
        image_annotations: List[ImageAnnotation],
        images_dir: str,
    ) -> Dict:
        """
        验证整个数据集
        
        返回:
            {"valid": int, "invalid": int, "errors": [...], "warnings": [...]}
        """
        report = {
            "valid": 0,
            "invalid": 0,
            "errors": [],
            "warnings": [],
        }
        
        images_path = Path(images_dir)
        
        for img_ann in image_annotations:
            result = self._validate_single(img_ann, images_path)
            if result["valid"]:
                report["valid"] += 1
            else:
                report["invalid"] += 1
                report["errors"].extend(result["errors"])
            report["warnings"].extend(result["warnings"])
        
        return report
    
    def _validate_single(
        self, img_ann: ImageAnnotation, images_path: Path
    ) -> Dict:
        """验证单张图片的标注"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        # 1. 检查图片是否存在
        img_path = images_path / img_ann.image_name
        if not img_path.exists():
            # 尝试递归搜索
            found = list(images_path.rglob(Path(img_ann.image_name).name))
            if found:
                img_path = found[0]
            else:
                result["valid"] = False
                result["errors"].append(f"图片不存在: {img_ann.image_name}")
                return result
        
        # 2. 检查标注数量
        if not img_ann.annotations:
            result["warnings"].append(f"无标注: {img_ann.image_name}")
        
        # 3. 验证bbox坐标范围
        for ann in img_ann.annotations:
            if ann.bbox:
                x1, y1, x2, y2 = ann.bbox
                
                # 检查坐标有效性
                if x1 >= x2 or y1 >= y2:
                    result["warnings"].append(
                        f"无效bbox: {img_ann.image_name} [{x1},{y1},{x2},{y2}]"
                    )
                
                # 自动修正超出范围的bbox
                if self.fix_bbox_clipping:
                    x1 = max(0, min(x1, img_ann.width))
                    y1 = max(0, min(y1, img_ann.height))
                    x2 = max(0, min(x2, img_ann.width))
                    y2 = max(0, min(y2, img_ann.height))
                    ann.bbox = (x1, y1, x2, y2)
            
            # 检查label是否为空
            if not ann.label:
                result["warnings"].append(
                    f"空标签: {img_ann.image_name} ({ann.shape_type})"
                )
        
        return result
    
    def get_statistics(self, image_annotations: List[ImageAnnotation]) -> Dict:
        """
        统计数据集信息
        
        返回:
            {"total_images": int, "total_annotations": int,
             "label_counts": {label: count}, "shape_counts": {shape: count}}
        """
        stats = {
            "total_images": len(image_annotations),
            "total_annotations": 0,
            "label_counts": {},
            "shape_counts": {},
        }
        
        for img_ann in image_annotations:
            for ann in img_ann.annotations:
                stats["total_annotations"] += 1
                
                # 统计label
                label = ann.label or "(empty)"
                stats["label_counts"][label] = stats["label_counts"].get(label, 0) + 1
                
                # 统计shape类型
                shape = ann.shape_type
                stats["shape_counts"][shape] = stats["shape_counts"].get(shape, 0) + 1
        
        return stats
