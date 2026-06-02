"""
训练集/验证集划分
==================
按图片级别划分, 确保同一图片生成的所有QA对归入同一集合。

支持两种划分策略:
    1. 随机划分 (默认)
    2. 分层抽样 (按类别分布划分, 保证训练/验证集类别分布一致)
"""

import random
from typing import List, Dict, Tuple
from collections import defaultdict


class DatasetSplitter:
    """
    数据集划分器
    
    使用方法:
        splitter = DatasetSplitter(seed=42)
        train, val = splitter.split(samples, train_ratio=0.9)
    
    参数:
        seed: 随机种子 (确保可复现)
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
    
    def split(
        self,
        samples: List[Dict],
        train_ratio: float = 0.9,
        stratify_by_label: bool = False,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        将样本列表划分为训练集和验证集
        
        参数:
            samples:            样本列表 (每个元素为一个QA对字典)
            train_ratio:        训练集占比 (0.0~1.0)
            stratify_by_label:  是否按标签分层抽样
            
        返回:
            (train_samples, val_samples)
        """
        if not samples:
            return [], []
        
        # 按图片分组
        image_groups = self._group_by_image(samples)
        image_keys = list(image_groups.keys())
        
        if stratify_by_label:
            train_keys, val_keys = self._stratified_split(
                image_keys, image_groups, train_ratio
            )
        else:
            train_keys, val_keys = self._random_split(image_keys, train_ratio)
        
        train_samples = [s for k in train_keys for s in image_groups[k]]
        val_samples = [s for k in val_keys for s in image_groups[k]]
        
        return train_samples, val_samples
    
    def _group_by_image(self, samples: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按图片标识将样本分组
        
        识别图片标识的逻辑:
        1. swift格式: sample["images"][0]
        2. unsloth格式: 从messages中提取image路径
        """
        groups = defaultdict(list)
        for sample in samples:
            key = self._get_image_key(sample)
            groups[key].append(sample)
        return dict(groups)
    
    def _get_image_key(self, sample: Dict) -> str:
        """从sample中提取图片唯一标识"""
        # swift格式
        if "images" in sample and sample["images"]:
            return sample["images"][0]
        
        # unsloth格式: 从messages中提取
        for msg in sample.get("messages", []):
            content = msg.get("content", [])
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "image":
                        return str(c.get("image", ""))
            elif isinstance(content, str):
                # 如果是纯文本格式, 用content hash
                pass
        
        # fallback: 用整个sample的hash
        return str(id(sample))
    
    def _random_split(
        self, keys: List[str], train_ratio: float
    ) -> Tuple[List[str], List[str]]:
        """随机划分"""
        rng = random.Random(self.seed)
        shuffled = keys.copy()
        rng.shuffle(shuffled)
        
        split_idx = int(len(shuffled) * train_ratio)
        return shuffled[:split_idx], shuffled[split_idx:]
    
    def _stratified_split(
        self,
        keys: List[str],
        image_groups: Dict[str, List[Dict]],
        train_ratio: float,
    ) -> Tuple[List[str], List[str]]:
        """
        分层抽样划分
        
        确保训练集和验证集的类别分布尽量一致。
        策略: 以每张图片的"主要类别"作为分层依据。
        """
        # 为每张图片确定主要类别
        label_to_keys = defaultdict(list)
        for key in keys:
            samples = image_groups[key]
            # 统计该图片的所有类别, 取出现最多的
            label_counts = defaultdict(int)
            for s in samples:
                label = self._extract_primary_label(s)
                if label:
                    label_counts[label] += 1
            
            if label_counts:
                primary_label = max(label_counts, key=label_counts.get)
            else:
                primary_label = "__no_label__"
            
            label_to_keys[primary_label].append(key)
        
        # 对每个类别分别进行随机划分
        train_keys, val_keys = [], []
        rng = random.Random(self.seed)
        
        for label, label_keys in label_to_keys.items():
            shuffled = label_keys.copy()
            rng.shuffle(shuffled)
            
            split_idx = int(len(shuffled) * train_ratio)
            train_keys.extend(shuffled[:split_idx])
            val_keys.extend(shuffled[split_idx:])
        
        return train_keys, val_keys
    
    def _extract_primary_label(self, sample: Dict) -> str:
        """从样本中提取主要标签"""
        # swift格式: objects.ref
        if "objects" in sample:
            refs = sample["objects"].get("ref", [])
            if refs:
                return refs[0]
        
        # unsloth格式: 从assistant回复中提取label
        for msg in sample.get("messages", []):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            text = c.get("text", "")
                            if '"label"' in text:
                                # 简单提取第一个label
                                import re
                                match = re.search(r'"label":\s*"([^"]+)"', text)
                                if match:
                                    return match.group(1)
                elif isinstance(content, str):
                    if '"label"' in content:
                        import re
                        match = re.search(r'"label":\s*"([^"]+)"', content)
                        if match:
                            return match.group(1)
        
        return ""
