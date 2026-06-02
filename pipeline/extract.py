"""
ZIP解压与多数据集合并
=====================
处理逻辑:
    1. 逐个解压ZIP到临时目录
    2. 自动检测 images/ 目录和 annotations.xml 位置
    3. 复制images到统一目录 (保留子目录结构)
    4. 合并多个annotations.xml (重新编号image id, 加前缀避免文件名冲突)

支持的ZIP内部结构:
    xxx.zip
    ├── images/              (或 images/, 或根目录直接放图片)
    │   ├── 001.jpg
    │   └── subdir/
    │       └── 002.jpg
    └── annotations.xml
"""

import zipfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple


class DatasetExtractor:
    """
    从多个ZIP/目录中提取并合并CVAT数据集
    
    使用方法:
        extractor = DatasetExtractor()
        merged_dir = extractor.extract_and_merge(
            input_paths=["data/dataset1.zip", "data/dataset2.zip"],
            output_dir="./output"
        )
    
    输出目录结构:
        output/merged/
        ├── images/
        │   ├── dataset1_001.jpg
        │   ├── dataset1_subdir_002.jpg
        │   └── dataset2_003.jpg
        └── annotations.xml  (合并后的)
    """
    
    SUPPORTED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    def extract_and_merge(
        self,
        input_paths: List[str],
        output_dir: str,
        prefix_with_dataset_name: bool = True,
    ) -> str:
        """
        解压并合并多个数据集
        
        参数:
            input_paths:            ZIP文件或已解压目录的路径列表
            output_dir:             输出根目录
            prefix_with_dataset_name: 是否在文件名前加数据集前缀 (避免冲突)
            
        返回:
            合并后的数据集根目录路径 (包含 images/ 和 annotations.xml)
        """
        merged_dir = Path(output_dir) / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)
        
        images_dir = merged_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        all_image_entries = []  # [(relative_path, source_dataset_name)]
        all_xml_roots = []      # [(ET.Element, dataset_name, image_id_offset)]
        current_id_offset = 0
        
        for input_path in input_paths:
            path = Path(input_path)
            dataset_name = path.stem if path.is_file() else path.name
            
            # 解压ZIP或直接使用目录
            if path.is_file() and path.suffix.lower() == '.zip':
                extract_dir = self._extract_zip(path, merged_dir)
            elif path.is_dir():
                extract_dir = path
            else:
                print(f"[WARN] 跳过无法处理的路径: {input_path}")
                continue
            
            # 检测结构并提取信息
            xml_path, images_subdir = self._detect_structure(extract_dir)
            
            if xml_path is None:
                print(f"[WARN] 在 {extract_dir} 中未找到 annotations.xml, 跳过")
                continue
            
            # 复制图片
            image_entries = self._copy_images(
                images_subdir, images_dir, dataset_name,
                prefix_with_dataset_name
            )
            all_image_entries.extend(image_entries)
            
            # 解析XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            all_xml_roots.append((root, dataset_name, current_id_offset))
            
            # 计算id偏移量
            max_id = self._get_max_image_id(root)
            current_id_offset += max_id + 1
        
        # 合并所有XML
        merged_xml = self._merge_xmls(all_xml_roots, all_image_entries)
        merged_xml_path = merged_dir / "annotations.xml"
        ET.ElementTree(merged_xml).write(merged_xml_path, encoding='utf-8', xml_declaration=True)
        
        # 清理解压的临时目录 (避免parser重复扫描)
        for input_path in input_paths:
            path = Path(input_path)
            if path.is_file() and path.suffix.lower() == '.zip':
                extract_dir = merged_dir / f"extract_{path.stem}"
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
        
        print(f"[INFO] 合并完成: {len(all_image_entries)} 张图片, 输出目录: {merged_dir}")
        return str(merged_dir)
    
    def _extract_zip(self, zip_path: Path, target_dir: Path) -> Path:
        """解压ZIP到目标目录, 返回解压后的根目录"""
        extract_dir = target_dir / f"extract_{zip_path.stem}"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        
        return extract_dir
    
    def _detect_structure(self, extract_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
        """
        自动检测annotations.xml和images目录的位置
        
        返回:
            (xml_path, images_dir) 或 (None, None)
        """
        # 查找annotations.xml (递归搜索, 取第一个)
        xml_files = list(extract_dir.rglob("annotations.xml"))
        xml_path = xml_files[0] if xml_files else None
        
        # 查找images目录
        images_dir = None
        # 优先查找名为"images"的目录
        for d in extract_dir.rglob("images"):
            if d.is_dir():
                images_dir = d
                break
        
        # 如果没有images目录, 查找包含图片文件的目录
        if images_dir is None:
            for d in [extract_dir] + list(extract_dir.rglobs("*")):
                if d.is_dir():
                    img_files = [f for f in d.iterdir()
                                 if f.is_file() and f.suffix.lower() in self.SUPPORTED_IMAGE_EXTS]
                    if img_files:
                        images_dir = d
                        break
        
        return xml_path, images_dir
    
    def _copy_images(
        self,
        source_dir: Optional[Path],
        target_dir: Path,
        dataset_name: str,
        prefix_with_dataset_name: bool,
    ) -> List[str]:
        """
        从源目录复制图片到目标目录
        
        返回:
            复制的图片相对路径列表 (相对于target_dir的父目录)
        """
        entries = []
        if source_dir is None:
            return entries
        
        for img_file in source_dir.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in self.SUPPORTED_IMAGE_EXTS:
                # 构造目标文件名 (加前缀避免冲突)
                if prefix_with_dataset_name:
                    # 保留子目录结构: subdir/file.jpg → datasetname_subdir_file.jpg
                    rel_path = img_file.relative_to(source_dir)
                    parts = list(rel_path.parts)
                    # 始终加数据集前缀, 避免不同ZIP中同名文件冲突
                    parts[0] = f"{dataset_name}_{parts[0]}"
                    new_name = "_".join(parts)
                else:
                    new_name = img_file.name
                
                dest = target_dir / new_name
                if not dest.exists():
                    shutil.copy2(img_file, dest)
                
                entries.append(new_name)
        
        return entries
    
    def _get_max_image_id(self, root: ET.Element) -> int:
        """获取XML中最大的image id"""
        max_id = 0
        for img_elem in root.findall('image'):
            try:
                img_id = int(img_elem.get('id', 0))
                max_id = max(max_id, img_id)
            except (ValueError, TypeError):
                pass
        return max_id
    
    def _merge_xmls(
        self,
        xml_roots: List[Tuple[ET.Element, str, int]],
        image_entries: List[str],
    ) -> ET.Element:
        """
        合并多个annotations.xml的根元素
        
        处理:
        1. 创建新的<annotations>根元素
        2. 合并所有<image>节点, 重新编号id
        3. 更新image name为新的文件名
        4. 保留meta信息 (取第一个)
        """
        merged = ET.Element('annotations')
        merged.set('version', '1.1')
        
        # 取第一个XML的meta信息
        if xml_roots:
            first_root = xml_roots[0][0]
            meta = first_root.find('meta')
            if meta is not None:
                merged.append(meta)
        
        # 合并所有image节点
        image_id_counter = 0
        for root, dataset_name, id_offset in xml_roots:
            for img_elem in root.findall('image'):
                # 创建新的image元素
                new_img = ET.SubElement(merged, 'image')
                new_img.set('id', str(image_id_counter))
                
                # 更新name: 使用复制后的新文件名
                old_name = img_elem.get('name', '')
                old_stem = Path(old_name).stem
                new_name = f"{dataset_name}_{old_stem}{Path(old_name).suffix}"
                new_img.set('name', new_name)
                
                new_img.set('width', img_elem.get('width', '0'))
                new_img.set('height', img_elem.get('height', '0'))
                
                # 复制所有标注子元素
                for child in img_elem:
                    new_img.append(child)
                
                image_id_counter += 1
        
        return merged
