"""
QA对生成器
==========
从CVAT标注生成两种微调任务的QA对:

Task 1: Grounding + 描述
    输入: 图像
    输出: 所有物体的bbox坐标 + 类别名称 (JSON格式)

Task 2: 框内物体验证
    输入: 图像 + bbox坐标 + 提示词
    输出: 判断该位置物体是否符合提示词描述

支持两种框架格式:
    - "swift":   ms-swift JSONL格式 (bbox用绝对坐标, 框架自动归一化到模型coord_range)
    - "unsloth": Unsloth格式 (bbox需手动归一化到模型coord_range写入text)

支持的模型:
    - Qwen2.5-VL / Qwen3-VL / Qwen3.5-VL / Qwen3.6-VL
    - 所有模型共用同一套数据格式 (0-1000 归一化)
    - 差异点 (patch_size等) 在训练侧处理, 与数据预处理无关
"""

import random
from typing import List, Dict, Optional

from parsers.cvat_parser import Annotation, ImageAnnotation
from converters.coord_converter import (
    polygon_to_bbox,
    annotation_to_bbox,
    normalize_bbox_to_1000,
    normalize_bbox_for_model,
)
from model_registry import get_coord_range


# ======================== QA模板库 ========================

# Task 1: Grounding 模板
GROUNDING_TEMPLATES = [
    "请定位图像中的所有物体，并给出边界框和类别。",
    "检测图中包含的所有目标，输出其位置和类别名称。",
    "请找出图像中的每一个物体，以JSON格式输出bbox和label。",
    "请对图像中的所有目标进行检测，输出边界框坐标和类别。",
]

# Task 1: 单类别Grounding模板
SINGLE_LABEL_TEMPLATES = [
    "请找到图像中的{label}，输出其边界框坐标。",
    "图中有哪些{label}？请给出它们的位置。",
    "检测图像中所有的{label}，输出其bbox坐标。",
]

# Task 2: 框内物体验证模板 (正例/负例通用)
VERIFICATION_TEMPLATES = [
    "请判断图中[{x1},{y1},{x2},{y2}]位置的物体是否是{label}。给出判断和理由。",
    "图中坐标[{x1},{y1},{x2},{y2}]处的物体看起来像{label}吗？请分析其外观特征。",
    "验证：位置[{x1},{y1},{x2},{y2}]内的目标是否符合「{label}」的描述？",
]

# Task 2: 描述框内物体模板
DESCRIBE_BBOX_TEMPLATES = [
    "请描述图中[{x1},{y1},{x2},{y2}]位置的物体是什么。",
    "图中[{x1},{y1},{x2},{y2}]区域内有什么？请详细描述其外观。",
]

# Task 2: OCR模板 (当attribute中有ocr_text时使用)
OCR_TEMPLATES = [
    "请读取图中[{x1},{y1},{x2},{y2}]位置的文字内容。",
    "图中[{x1},{y1},{x2},{y2}]区域内的文字是什么？",
]


class QAGenerator:
    """
    QA对生成器

    使用方法:
        generator = QAGenerator(target_framework="swift", model_name="Qwen3-VL-8B-Instruct")
        samples = generator.generate(img_annotation)

    参数:
        target_framework:    目标框架 ("swift" 或 "unsloth")
        model_name:          目标模型名称 (决定 coord_range), 默认 Qwen3-VL-8B-Instruct
        enable_grounding:    是否生成Task 1 (grounding)数据
        enable_verification: 是否生成Task 2 (验证)数据
        neg_sample_ratio:    负例样本占比 (0.0~0.5)
        max_objects_per_image: 单张图片最大物体数 (超过则截断)
    """

    def __init__(
        self,
        target_framework: str = "swift",
        model_name: str = "Qwen3-VL-8B-Instruct",
        enable_grounding: bool = True,
        enable_verification: bool = True,
        neg_sample_ratio: float = 0.3,
        max_objects_per_image: int = 50,
    ):
        assert target_framework in ("swift", "unsloth"), \
            f"target_framework must be 'swift' or 'unsloth', got '{target_framework}'"

        self.target_framework = target_framework
        self.model_name = model_name
        self.coord_range = get_coord_range(model_name)
        self.enable_grounding = enable_grounding
        self.enable_verification = enable_verification
        self.neg_sample_ratio = neg_sample_ratio
        self.max_objects_per_image = max_objects_per_image

    def _normalize(self, bbox, img_w, img_h):
        """根据目标模型归一化bbox (delegates to model_registry)"""
        return normalize_bbox_for_model(bbox, img_w, img_h, self.model_name)

    def generate(self, img_ann: ImageAnnotation) -> List[Dict]:
        """
        为一张图片生成所有QA对

        参数:
            img_ann: ImageAnnotation对象 (来自CVATParser)

        返回:
            QA对列表, 每个元素为一个字典 (格式取决于target_framework)
        """
        samples = []

        bbox_annotations = self._collect_bbox_annotations(img_ann)

        if self.enable_grounding and bbox_annotations:
            samples.extend(self._gen_grounding(img_ann, bbox_annotations))

        if self.enable_verification and bbox_annotations:
            samples.extend(self._gen_verification(img_ann, bbox_annotations))

        return samples

    def _collect_bbox_annotations(self, img_ann: ImageAnnotation) -> List[Dict]:
        """从ImageAnnotation中收集所有可转换为bbox的标注"""
        results = []
        for ann in img_ann.annotations:
            bbox = annotation_to_bbox(ann)
            if bbox is not None:
                results.append({
                    "annotation": ann,
                    "bbox": bbox,
                    "label": ann.label,
                })

        if len(results) > self.max_objects_per_image:
            results = results[:self.max_objects_per_image]

        return results

    # ======================== Task 1: Grounding ========================

    def _gen_grounding(
        self, img_ann: ImageAnnotation, bbox_anns: List[Dict]
    ) -> List[Dict]:
        """
        生成Grounding QA对

        ms-swift格式:
            {"messages": [...], "images": [...], "objects": {"ref": [...], "bbox": [...]}}

        Unsloth格式:
            {"messages": [{"role":"user","content":[{"type":"text","text":...},{"type":"image","image":PIL}]},
                          {"role":"assistant","content":[{"type":"text","text":...}]}]}
        """
        sample = []

        template = random.choice(GROUNDING_TEMPLATES)
        all_labels = [a["label"] for a in bbox_anns]
        all_bboxes = [a["bbox"] for a in bbox_anns]

        if self.target_framework == "swift":
            answer_items = []
            for bbox, label in zip(all_bboxes, all_labels):
                answer_items.append(f'{{"bbox_2d": {list(map(round, bbox))}, "label": "{label}"}}')
            answer_text = "[\n" + ",\n".join(f"\t{item}" for item in answer_items) + "\n]"

            sample.append(self._make_swift_sample(
                user_text=f"<image>{template}",
                answer_text=answer_text,
                image_path=img_ann.image_name,
                objects={"ref": all_labels, "bbox": [list(b) for b in all_bboxes]},
            ))
        else:  # unsloth
            normalized_bboxes = [
                list(self._normalize(b, img_ann.width, img_ann.height))
                for b in all_bboxes
            ]
            norm_answer_items = []
            for bbox, label in zip(normalized_bboxes, all_labels):
                norm_answer_items.append(f'{{"bbox_2d": {bbox}, "label": "{label}"}}')
            norm_answer_text = "[\n" + ",\n".join(f"\t{item}" for item in norm_answer_items) + "\n]"

            sample.append(self._make_unsloth_sample(
                user_text=template,
                answer_text=norm_answer_text,
                image_path=img_ann.image_name,
            ))

        label_counts = {}
        for a in bbox_anns:
            label_counts[a["label"]] = label_counts.get(a["label"], 0) + 1

        for label, count in label_counts.items():
            if count >= 2:
                tmpl = random.choice(SINGLE_LABEL_TEMPLATES).format(label=label)
                matched_bboxes = [a["bbox"] for a in bbox_anns if a["label"] == label]

                if self.target_framework == "swift":
                    single_answer_items = [
                        f'{{"bbox_2d": {list(map(round, b))}, "label": "{label}"}}'
                        for b in matched_bboxes
                    ]
                    single_answer = "[\n" + ",\n".join(f"\t{item}" for item in single_answer_items) + "\n]"

                    sample.append(self._make_swift_sample(
                        user_text=f"<image>{tmpl}",
                        answer_text=single_answer,
                        image_path=img_ann.image_name,
                        objects={"ref": [label]*len(matched_bboxes),
                                 "bbox": [list(b) for b in matched_bboxes]},
                    ))
                else:
                    norm_bboxes = [
                        list(self._normalize(b, img_ann.width, img_ann.height))
                        for b in matched_bboxes
                    ]
                    norm_single_items = [
                        f'{{"bbox_2d": {nb}, "label": "{label}"}}'
                        for nb in norm_bboxes
                    ]
                    norm_single_answer = "[\n" + ",\n".join(f"\t{item}" for item in norm_single_items) + "\n]"
                    sample.append(self._make_unsloth_sample(
                        user_text=tmpl,
                        answer_text=norm_single_answer,
                        image_path=img_ann.image_name,
                    ))

        return sample

    # ======================== Task 2: 框内物体验证 ========================

    def _gen_verification(
        self, img_ann: ImageAnnotation, bbox_anns: List[Dict]
    ) -> List[Dict]:
        """
        生成框内物体验证 QA对

        正例: label正确 → "是的, 该物体是{label}"
        负例: 随机替换label → "不是, 该物体是{true_label}, 不是{wrong_label}"
        """
        samples = []
        all_labels = list(set(a["label"] for a in bbox_anns))

        for ann_info in bbox_anns:
            bbox = ann_info["bbox"]
            label = ann_info["label"]

            template = random.choice(VERIFICATION_TEMPLATES)
            user_text = template.format(
                x1=round(bbox[0]), y1=round(bbox[1]),
                x2=round(bbox[2]), y2=round(bbox[3]),
                label=label
            )
            pos_answer = f"是的, 该位置的物体是{label}。从外观特征看, 它具有{label}的典型结构和特征。"

            if self.target_framework == "swift":
                samples.append(self._make_swift_sample(
                    user_text=f"<image>{user_text}",
                    answer_text=pos_answer,
                    image_path=img_ann.image_name,
                ))
            else:
                norm_bbox = list(self._normalize(bbox, img_ann.width, img_ann.height))
                norm_user_text = f"请判断图中[{norm_bbox[0]},{norm_bbox[1]},{norm_bbox[2]},{norm_bbox[3]}]位置的物体是否是{label}。给出判断和理由。"
                samples.append(self._make_unsloth_sample(
                    user_text=norm_user_text,
                    answer_text=pos_answer,
                    image_path=img_ann.image_name,
                ))

            if len(all_labels) > 1 and random.random() < self.neg_sample_ratio:
                wrong_labels = [l for l in all_labels if l != label]
                wrong_label = random.choice(wrong_labels)

                neg_answer = f"不是, 该位置的物体是{label}, 不是{wrong_label}。从外观特征看, 它具有{label}的典型结构, 与{wrong_label}的特征不符。"

                neg_template = random.choice(VERIFICATION_TEMPLATES)
                neg_user_text = neg_template.format(
                    x1=round(bbox[0]), y1=round(bbox[1]),
                    x2=round(bbox[2]), y2=round(bbox[3]),
                    label=wrong_label
                )

                if self.target_framework == "swift":
                    samples.append(self._make_swift_sample(
                        user_text=f"<image>{neg_user_text}",
                        answer_text=neg_answer,
                        image_path=img_ann.image_name,
                    ))
                else:
                    norm_user_neg = f"请判断图中[{norm_bbox[0]},{norm_bbox[1]},{norm_bbox[2]},{norm_bbox[3]}]位置的物体是否是{wrong_label}。给出判断和理由。"
                    samples.append(self._make_unsloth_sample(
                        user_text=norm_user_neg,
                        answer_text=neg_answer,
                        image_path=img_ann.image_name,
                    ))

        return samples

    # ======================== 格式构造 ========================

    def _make_swift_sample(
        self,
        user_text: str,
        answer_text: str,
        image_path: str,
        objects: Optional[Dict] = None,
    ) -> Dict:
        """
        构造ms-swift JSONL格式的样本

        格式 (适用于所有 Qwen2.5-VL+ 模型):
            {"messages": [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}],
             "images": ["path/to/img.jpg"],
             "objects": {"ref": [...], "bbox": [...]}}  (仅grounding任务有)
        """
        sample = {
            "messages": [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": answer_text},
            ],
            "images": [image_path],
        }
        if objects:
            sample["objects"] = objects
        return sample

    def _make_unsloth_sample(
        self,
        user_text: str,
        answer_text: str,
        image_path: str,
    ) -> Dict:
        """
        构造Unsloth格式的样本

        格式:
            {"messages": [{"role":"user","content":[{"type":"text","text":...},{"type":"image","image":PIL}]},
                          {"role":"assistant","content":[{"type":"text","text":...}]}]}

        注意:
            - image字段存储的是**文件路径字符串**, 后续由main.py负责转为PIL.Image
            - bbox已手动归一化到该模型的 coord_range (默认1000), 写入assistant的text中
        """
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image", "image": image_path},
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": answer_text}
                    ]
                },
            ]
        }
