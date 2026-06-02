"""
cvat2qwen3vl 主入口
====================
CVAT标注 → Qwen3-VL微调数据 全流程处理

流程:
    1. 读取配置
    2. 解压并合并多个ZIP数据集
    3. 解析所有annotations.xml
    4. 数据验证
    5. 生成QA对 (同时输出swift和unsloth格式)
    6. 划分训练集/验证集
    7. 输出JSONL/JSON文件
    8. 打印统计信息
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

import yaml

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.cvat_parser import CVATParser, ImageAnnotation
from converters.qa_generator import QAGenerator
from pipeline.extract import DatasetExtractor
from pipeline.validate import DataValidator
from pipeline.splitter import DatasetSplitter


def load_config(config_path: str = "config.yaml") -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main(config_path: str = "config.yaml"):
    """主流程"""
    print("=" * 60)
    print("  cvat2qwen3vl - CVAT标注转Qwen3-VL微调数据")
    print("=" * 60)
    
    # ==================== 1. 加载配置 ====================
    config = load_config(config_path)
    print(f"\n[1/7] 加载配置: {config_path}")
    
    input_paths = config.get('input_paths', [])
    output_dir = config.get('output_dir', './output')
    frameworks = config.get('frameworks', ['swift'])
    tasks = config.get('tasks', {})
    split_config = config.get('split_ratio', {})
    val_config = config.get('validation', {})
    
    if not input_paths:
        print("[ERROR] 未配置输入路径 (input_paths), 请编辑 config.yaml")
        return
    
    print(f"  输入路径: {input_paths}")
    print(f"  输出目录: {output_dir}")
    print(f"  目标框架: {frameworks}")
    print(f"  任务类型: grounding={tasks.get('grounding', True)}, "
          f"verification={tasks.get('verification', True)}")
    
    # ==================== 2. 解压合并 ====================
    print(f"\n[2/7] 解压并合并数据集...")
    extractor = DatasetExtractor()
    merged_dir = extractor.extract_and_merge(
        input_paths=input_paths,
        output_dir=output_dir,
    )
    print(f"  合并目录: {merged_dir}")
    
    # ==================== 3. 解析标注 ====================
    print(f"\n[3/7] 解析annotations.xml...")
    parser = CVATParser()
    all_img_anns: List[ImageAnnotation] = parser.parse_directory(merged_dir)
    print(f"  解析完成: {len(all_img_anns)} 张图片")
    
    # ==================== 4. 数据验证 ====================
    print(f"\n[4/7] 数据验证...")
    validator = DataValidator(
        fix_bbox_clipping=val_config.get('fix_bbox_clipping', True)
    )
    report = validator.validate(all_img_anns, str(Path(merged_dir) / "images"))
    stats = validator.get_statistics(all_img_anns)
    
    print(f"  有效图片: {report['valid']}")
    print(f"  无效图片: {report['invalid']}")
    print(f"  总标注数: {stats['total_annotations']}")
    print(f"  类别分布: {dict(sorted(stats['label_counts'].items(), key=lambda x: -x[1])[:10])}")
    print(f"  标注类型: {stats['shape_counts']}")
    
    if report['warnings']:
        print(f"  警告数量: {len(report['warnings'])}")
        for w in report['warnings'][:5]:
            print(f"    - {w}")
    
    if report['errors']:
        print(f"  错误列表:")
        for e in report['errors'][:10]:
            print(f"    - {e}")
    
    # 过滤掉无效图片
    valid_img_anns = [ann for ann in all_img_anns
                      if ann.annotations or not val_config.get('skip_empty_annotations', False)]
    
    # ==================== 5. 生成QA对 ====================
    print(f"\n[5/7] 生成QA对...")
    
    for framework in frameworks:
        print(f"\n  --- 框架: {framework} ---")
        
        generator = QAGenerator(
            target_framework=framework,
            enable_grounding=tasks.get('grounding', True),
            enable_verification=tasks.get('verification', True),
            neg_sample_ratio=tasks.get('neg_sample_ratio', 0.3),
        )
        
        all_samples: List[Dict] = []
        for img_ann in valid_img_anns:
            samples = generator.generate(img_ann)
            all_samples.extend(samples)
        
        print(f"  生成样本数: {len(all_samples)}")
        
        # ==================== 6. 划分数据集 ====================
        print(f"\n[6/7] 划分训练集/验证集...")
        
        splitter = DatasetSplitter(seed=split_config.get('seed', 42))
        train_samples, val_samples = splitter.split(
            all_samples,
            train_ratio=split_config.get('train', 0.9),
            stratify_by_label=split_config.get('stratify_by_label', False),
        )
        
        print(f"  训练集: {len(train_samples)} 样本")
        print(f"  验证集: {len(val_samples)} 样本")
        
        # ==================== 7. 输出文件 ====================
        print(f"\n[7/7] 输出文件...")
        
        out_dir = Path(output_dir) / framework
        out_dir.mkdir(parents=True, exist_ok=True)
        
        if framework == "swift":
            train_path = out_dir / "train.jsonl"
            val_path = out_dir / "val.jsonl"
            _write_jsonl(train_samples, train_path)
            _write_jsonl(val_samples, val_path)
        else:  # unsloth
            train_path = out_dir / "train.json"
            val_path = out_dir / "val.json"
            _write_json(train_samples, train_path)
            _write_json(val_samples, val_path)
        
        print(f"  训练文件: {train_path}")
        print(f"  验证文件: {val_path}")
        
        # 输出样本示例
        if train_samples:
            print(f"\n  样本示例 (第1条):")
            _print_sample_preview(train_samples[0], framework)
    
    # ==================== 汇总 ====================
    print("\n" + "=" * 60)
    print("  处理完成!")
    print("=" * 60)
    print(f"  输出目录: {output_dir}")
    print(f"  下一步:")
    print(f"    1. 检查输出文件内容是否正确")
    print(f"    2. 运行训练脚本:")
    for framework in frameworks:
        if framework == "swift":
            print(f"       bash scripts/train_swift.sh")
        else:
            print(f"       python scripts/train_unsloth.py")


def _write_jsonl(samples: List[Dict], path: Path):
    """写入JSONL文件"""
    with open(path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')


def _write_json(samples: List[Dict], path: Path):
    """写入JSON文件"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)


def _print_sample_preview(sample: Dict, framework: str):
    """打印样本预览"""
    if framework == "swift":
        messages = sample.get("messages", [])
        images = sample.get("images", [])
        objects = sample.get("objects", {})
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str):
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"    [{role}]: {preview}")
        
        if images:
            print(f"    [images]: {images}")
        if objects:
            print(f"    [objects]: ref={objects.get('ref', [])[:3]}..., "
                  f"bbox数量={len(objects.get('bbox', []))}")
    
    else:  # unsloth
        messages = sample.get("messages", [])
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", [])
            if isinstance(content, list):
                for c in content:
                    if c.get("type") == "text":
                        text = c["text"]
                        preview = text[:100] + "..." if len(text) > 100 else text
                        print(f"    [{role}/text]: {preview}")
                    elif c.get("type") == "image":
                        print(f"    [{role}/image]: {c.get('image', '')}")


if __name__ == "__main__":
    import argparse
    
    arg_parser = argparse.ArgumentParser(description="CVAT标注转Qwen3-VL微调数据")
    arg_parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = arg_parser.parse_args()
    
    main(args.config)
