"""
CVAT annotations.xml 解析器
============================
支持的标注类型:
  - box:       检测框 (xtl, ytl, xbr, ybr 绝对像素坐标)
  - polygon:   多边形分割 (点序列)
  - polyline:  折线 (点序列)
  - points:    关键点 (点序列)
  - tag:       标签 (图像级或对象级)
  - mask:      RLE编码掩码
  - skeleton:  骨架关键点

OCR值处理:
  OCR文本存储在<box>/<polygon>等元素的<attribute>子节点中,
  解析时统一提取到 Annotation.attributes 字典中。

坐标体系:
  所有坐标均为**绝对像素坐标**, 后续由 coord_converter 负责转换。
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path


@dataclass
class Annotation:
    """
    统一标注数据结构
    
    属性:
        label:          类别名称 (如 "car", "person")
        shape_type:     标注类型 (box/polygon/polyline/points/tag/mask/skeleton)
        bbox:           检测框 [xtl, ytl, xbr, ybr] 绝对像素, 仅box类型直接有值
        polygon_points: 多边形/折线/关键点的点序列 [(x0,y0), (x1,y1), ...]
        attributes:     属性字典, 包含OCR文本、颜色等 (从<attribute>子节点提取)
        occluded:       是否被遮挡
        z_order:        层级顺序 (越大越靠近相机)
        mask_rle:       RLE编码的掩码字符串
        mask_offset:    掩码偏移 (left, top, width, height)
    """
    label: str
    shape_type: str
    bbox: Optional[Tuple[float, float, float, float]] = None
    polygon_points: Optional[List[Tuple[float, float]]] = None
    attributes: dict = field(default_factory=dict)
    occluded: bool = False
    z_order: int = 0
    mask_rle: Optional[str] = None
    mask_offset: Optional[Tuple[int, int, int, int]] = None  # (left, top, w, h)


@dataclass
class ImageAnnotation:
    """
    单张图片的所有标注信息
    
    属性:
        image_id:     图片ID (从XML中读取, 可能不连续)
        image_name:   图片相对路径 (可能含子目录, 如 "subdir/img001.jpg")
        width:        图片原始宽度 (像素)
        height:       图片原始高度 (像素)
        annotations:  该图片上所有标注的列表
    """
    image_id: int
    image_name: str
    width: int
    height: int
    annotations: List[Annotation] = field(default_factory=list)


class CVATParser:
    """
    CVAT annotations.xml 解析器
    
    使用方法:
        parser = CVATParser()
        annotations = parser.parse("path/to/annotations.xml")
        for img_ann in annotations:
            print(f"{img_ann.image_name}: {len(img_ann.annotations)} annotations")
    
    注意事项:
        1. image[@name] 字段可能包含子目录路径
        2. box的xtl/ytl/xbr/ybr为浮点数, 表示绝对像素坐标
        3. polygon的points为分号分隔的 "x,y" 对
        4. <attribute>子节点的text可能为None (空属性), 统一转为空字符串
    """

    def parse(self, xml_path: str) -> List[ImageAnnotation]:
        """
        解析单个annotations.xml文件
        
        参数:
            xml_path: XML文件路径
            
        返回:
            ImageAnnotation列表, 每个元素对应一张图片
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        results = []
        for image_elem in root.findall('image'):
            img_ann = self._parse_image_element(image_elem)
            if img_ann is not None:
                results.append(img_ann)
        
        return results

    def parse_directory(self, dir_path: str) -> List[ImageAnnotation]:
        """
        解析目录下所有annotations.xml (递归搜索)
        
        参数:
            dir_path: 目录路径
            
        返回:
            所有图片的标注列表 (已合并)
        """
        all_annotations = []
        for xml_file in Path(dir_path).rglob("annotations.xml"):
            all_annotations.extend(self.parse(str(xml_file)))
        return all_annotations

    def _parse_image_element(self, elem: ET.Element) -> Optional[ImageAnnotation]:
        """
        解析<image>节点
        
        处理逻辑:
        1. 提取image属性 (id, name, width, height)
        2. 遍历所有子元素, 按tag类型分发到对应的解析方法
        3. 跳过无法识别的子元素 (如 <source>)
        """
        try:
            img_id = int(elem.get('id', 0))
            img_name = elem.get('name', '')
            width = int(elem.get('width', 0))
            height = int(elem.get('height', 0))
        except (ValueError, TypeError):
            return None
        
        img_ann = ImageAnnotation(
            image_id=img_id,
            image_name=img_name,
            width=width,
            height=height
        )
        
        # 解析所有标注子元素
        shape_parsers = {
            'box': self._parse_box,
            'polygon': self._parse_polygon,
            'polyline': self._parse_polyline,
            'points': self._parse_points,
            'tag': self._parse_tag,
            'mask': self._parse_mask,
            'skeleton': self._parse_skeleton,
        }
        
        for child in elem:
            parser_fn = shape_parsers.get(child.tag)
            if parser_fn:
                annotation = parser_fn(child)
                if annotation is not None:
                    img_ann.annotations.append(annotation)
        
        return img_ann

    def _parse_box(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<box>元素
        
        XML格式:
            <box label="car" xtl="100.0" ytl="200.0" xbr="500.0" ybr="400.0"
                 occluded="0" z_order="0">
                <attribute name="color">red</attribute>
                <attribute name="ocr_text">ABC-1234</attribute>
            </box>
        
        关键点:
            - xtl/ytl/xbr/ybr 为浮点数, 表示绝对像素坐标
            - <attribute>子节点的text可能为None
        """
        try:
            bbox = (
                float(elem.get('xtl', 0)),
                float(elem.get('ytl', 0)),
                float(elem.get('xbr', 0)),
                float(elem.get('ybr', 0))
            )
        except (ValueError, TypeError):
            return None
        
        return Annotation(
            label=elem.get('label', ''),
            shape_type='box',
            bbox=bbox,
            attributes=self._parse_attributes(elem),
            occluded=elem.get('occluded') == '1',
            z_order=int(elem.get('z_order', 0))
        )

    def _parse_polygon(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<polygon>元素
        
        XML格式:
            <polygon label="road" points="0,600;1920,600;1920,1080;0,1080"
                     occluded="0" z_order="1">
                <attribute name="type">asphalt</attribute>
            </polygon>
        
        关键点:
            - points 为分号分隔的 "x,y" 对
            - bbox 会自动计算外接矩形
        """
        points_str = elem.get('points', '')
        points = self._parse_points_string(points_str)
        
        if not points:
            return None
        
        return Annotation(
            label=elem.get('label', ''),
            shape_type='polygon',
            polygon_points=points,
            attributes=self._parse_attributes(elem),
            occluded=elem.get('occluded') == '1',
            z_order=int(elem.get('z_order', 0))
        )

    def _parse_polyline(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<polyline>元素 (折线, 与polygon类似但不闭合)
        
        XML格式:
            <polyline label="lane" points="0,600;1920,600" occluded="0" z_order="2"/>
        """
        points_str = elem.get('points', '')
        points = self._parse_points_string(points_str)
        
        if not points:
            return None
        
        return Annotation(
            label=elem.get('label', ''),
            shape_type='polyline',
            polygon_points=points,
            attributes=self._parse_attributes(elem),
            occluded=elem.get('occluded') == '1',
            z_order=int(elem.get('z_order', 0))
        )

    def _parse_points(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<points>元素 (关键点)
        
        XML格式:
            <points label="face" points="540,300;560,500;480,700" occluded="0"/>
        """
        points_str = elem.get('points', '')
        points = self._parse_points_string(points_str)
        
        if not points:
            return None
        
        return Annotation(
            label=elem.get('label', ''),
            shape_type='points',
            polygon_points=points,
            attributes=self._parse_attributes(elem),
            occluded=elem.get('occluded') == '1',
            z_order=int(elem.get('z_order', 0))
        )

    def _parse_tag(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<tag>元素 (标签, 无坐标信息)
        
        XML格式:
            <tag label="sunny" source="manual">
                <attribute name="time">morning</attribute>
            </tag>
        """
        return Annotation(
            label=elem.get('label', ''),
            shape_type='tag',
            attributes=self._parse_attributes(elem)
        )

    def _parse_mask(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<mask>元素 (RLE编码掩码)
        
        XML格式:
            <mask label="tree" source="manual" occluded="0"
                  rle="d0d0:F\0" left="0" top="0" width="100" height="100"/>
        """
        try:
            left = int(elem.get('left', 0))
            top = int(elem.get('top', 0))
            width = int(elem.get('width', 0))
            height = int(elem.get('height', 0))
        except (ValueError, TypeError):
            left, top, width, height = 0, 0, 0, 0
        
        return Annotation(
            label=elem.get('label', ''),
            shape_type='mask',
            mask_rle=elem.get('rle', ''),
            mask_offset=(left, top, width, height),
            attributes=self._parse_attributes(elem),
            occluded=elem.get('occluded') == '1',
            z_order=int(elem.get('z_order', 0))
        )

    def _parse_skeleton(self, elem: ET.Element) -> Optional[Annotation]:
        """
        解析<skeleton>元素 (骨架关键点)
        
        XML格式:
            <skeleton label="person" z_order="0">
                <points label="head" points="540,300" occluded="0"/>
                <points label="left_hand" points="480,700" occluded="0"/>
            </skeleton>
        """
        all_points = []
        for points_elem in elem.findall('points'):
            points_str = points_elem.get('points', '')
            pts = self._parse_points_string(points_str)
            all_points.extend(pts)
        
        if not all_points:
            return None
        
        return Annotation(
            label=elem.get('label', ''),
            shape_type='skeleton',
            polygon_points=all_points,
            attributes=self._parse_attributes(elem),
            z_order=int(elem.get('z_order', 0))
        )

    def _parse_attributes(self, elem: ET.Element) -> dict:
        """
        提取<attribute>子节点, 返回 {name: value} 字典
        
        关键点:
            - attribute的text可能为None (空值), 统一转为空字符串
            - 同名属性只保留最后一个值
        """
        attrs = {}
        for attr_elem in elem.findall('attribute'):
            name = attr_elem.get('name', '')
            value = attr_elem.text if attr_elem.text is not None else ""
            attrs[name] = value
        return attrs

    def _parse_points_string(self, points_str: str) -> List[Tuple[float, float]]:
        """
        将 "x0,y0;x1,y1;..." 格式的字符串解析为 [(x0,y0), (x1,y1), ...]
        
        参数:
            points_str: CVAT格式的点序列字符串
            
        返回:
            (x, y) 元组列表
        """
        if not points_str or not points_str.strip():
            return []
        
        points = []
        for pair in points_str.split(';'):
            pair = pair.strip()
            if not pair:
                continue
            try:
                x_str, y_str = pair.split(',')
                points.append((float(x_str.strip()), float(y_str.strip())))
            except ValueError:
                continue
        
        return points
