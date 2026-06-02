"""
Pipeline Runner
===============
将 cvat2qwen3vl pipeline 封装为 async generator，支持 WebSocket 进度推送。
每步 yield 事件字典，前端通过 WebSocket 实时接收。

支持多模型并行输出:
    - 按 frameworks 维度生成 (swift/unsloth)
    - 按 model_name 维度归一化 (决定 coord_range)
    - 默认 Qwen3-VL-8B-Instruct (coord_range=1000)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.cvat_parser import CVATParser, ImageAnnotation
from converters.qa_generator import QAGenerator
from pipeline.extract import DatasetExtractor
from pipeline.validate import DataValidator
from pipeline.splitter import DatasetSplitter
from model_registry import get_default_model, get_coord_range


async def run_pipeline_ws(
    input_paths: List[str],
    output_dir: str,
    config: Dict,
) -> AsyncGenerator[Dict, None]:
    """
    异步执行完整 pipeline，每步 yield 事件:
      {"type": "progress", "step": str, "progress": float}
      {"type": "log",      "message": str}
      {"type": "result",   "data": dict}
      {"type": "error",    "message": str}
    """
    try:
        # ====== Step 1: 解压合并 ======
        yield {"type": "progress", "step": "正在解压并合并数据集...", "progress": 0.0}
        yield {"type": "log", "message": "开始解压ZIP文件..."}

        extractor = DatasetExtractor()
        merged_dir = await asyncio.to_thread(
            extractor.extract_and_merge, input_paths, output_dir
        )
        yield {"type": "log", "message": f"合并完成: {merged_dir}"}

        # ====== Step 2: 解析标注 ======
        yield {"type": "progress", "step": "正在解析 annotations.xml...", "progress": 0.15}
        parser = CVATParser()
        all_img_anns: List[ImageAnnotation] = await asyncio.to_thread(
            parser.parse_directory, merged_dir
        )
        yield {"type": "log", "message": f"解析完成: {len(all_img_anns)} 张图片"}

        # ====== Step 3: 数据验证 ======
        yield {"type": "progress", "step": "正在验证数据...", "progress": 0.30}
        val_config = config.get("validation", {})
        validator = DataValidator(
            fix_bbox_clipping=val_config.get("fix_bbox_clipping", True)
        )
        images_dir = str(Path(merged_dir) / "images")
        report = await asyncio.to_thread(validator.validate, all_img_anns, images_dir)
        stats = await asyncio.to_thread(validator.get_statistics, all_img_anns)
        yield {
            "type": "log",
            "message": f"有效: {report['valid']}张, 标注: {stats['total_annotations']}个",
        }

        # 过滤空标注图片
        skip_empty = val_config.get("skip_empty_annotations", False)
        valid_anns = [a for a in all_img_anns if a.annotations or not skip_empty]

        # ====== Step 4-6: 生成QA + 划分 + 输出 (按框架) ======
        tasks_config = config.get("tasks", {})
        frameworks = config.get("frameworks", ["swift", "unsloth"])
        split_config = config.get("split_ratio", {})
        # 目标模型 (决定 coord_range), 默认 Qwen3-VL-8B-Instruct
        model_name = config.get("model_name") or get_default_model()
        coord_range = get_coord_range(model_name)

        yield {
            "type": "log",
            "message": f"目标模型: {model_name} (归一化范围: 0-{coord_range})",
        }

        output_files: Dict[str, str] = {}
        sample_counts: Dict[str, int] = {}
        train_counts: Dict[str, int] = {}
        val_counts: Dict[str, int] = {}
        final_train_samples = {}
        final_val_samples = {}

        for fi, framework in enumerate(frameworks):
            base = 0.40 + (fi / len(frameworks)) * 0.55
            yield {
                "type": "progress",
                "step": f"[{framework}] 正在生成QA对...",
                "progress": base,
            }

            generator = QAGenerator(
                target_framework=framework,
                model_name=model_name,
                enable_grounding=tasks_config.get("grounding", True),
                enable_verification=tasks_config.get("verification", True),
                neg_sample_ratio=tasks_config.get("neg_sample_ratio", 0.3),
            )

            all_samples: List[Dict] = []
            for ai, img_ann in enumerate(valid_anns):
                samples = await asyncio.to_thread(generator.generate, img_ann)
                all_samples.extend(samples)
                if (ai + 1) % 5 == 0 or ai == len(valid_anns) - 1:
                    sub = base + (ai + 1) / len(valid_anns) * 0.15
                    yield {
                        "type": "progress",
                        "step": f"[{framework}] QA生成: {ai+1}/{len(valid_anns)}",
                        "progress": min(sub, base + 0.15),
                    }

            sample_counts[framework] = len(all_samples)

            # 划分
            yield {
                "type": "progress",
                "step": f"[{framework}] 划分训练/验证集...",
                "progress": base + 0.15,
            }
            splitter = DatasetSplitter(seed=split_config.get("seed", 42))
            train_samples, val_samples = await asyncio.to_thread(
                splitter.split,
                all_samples,
                split_config.get("train", 0.9),
                split_config.get("stratify_by_label", False),
            )
            train_counts[framework] = len(train_samples)
            val_counts[framework] = len(val_samples)
            final_train_samples[framework] = train_samples
            final_val_samples[framework] = val_samples

            # 写文件 (按模型分子目录, 避免不同模型混在一起)
            yield {
                "type": "progress",
                "step": f"[{framework}] 写入文件...",
                "progress": base + 0.20,
            }
            # 用模型家族作为子目录 (e.g. swift/qwen3-vl/)
            model_dir_name = model_name.lower().split("-")[0] if "-" in model_name else model_name.lower()
            # 更稳健: 提取家族
            from model_registry import get_model
            meta = get_model(model_name)
            family = meta.get("family", "custom") if meta else "custom"
            out_dir = Path(output_dir) / framework / family
            out_dir.mkdir(parents=True, exist_ok=True)

            if framework == "swift":
                train_path = out_dir / "train.jsonl"
                val_path = out_dir / "val.jsonl"
                await asyncio.to_thread(_write_jsonl, train_samples, train_path)
                await asyncio.to_thread(_write_jsonl, val_samples, val_path)
            else:
                train_path = out_dir / "train.json"
                val_path = out_dir / "val.json"
                await asyncio.to_thread(_write_json, train_samples, train_path)
                await asyncio.to_thread(_write_json, val_samples, val_path)

            output_files[f"{framework}_train"] = str(train_path)
            output_files[f"{framework}_val"] = str(val_path)
            yield {
                "type": "log",
                "message": (
                    f"[{framework}/{family}] 完成: "
                    f"train={len(train_samples)}, val={len(val_samples)}"
                ),
            }

        # 构造预览样本 (取第一个framework的第一个样本)
        sample_preview = None
        for fw in frameworks:
            if fw in final_train_samples and final_train_samples[fw]:
                sample_preview = final_train_samples[fw][0]
                break

        # 返回最终结果
        yield {
            "type": "result",
            "data": {
                "stats": stats,
                "validation": report,
                "output_files": output_files,
                "sample_counts": sample_counts,
                "train_counts": train_counts,
                "val_counts": val_counts,
                "sample_preview": sample_preview,
                "model_name": model_name,
                "coord_range": coord_range,
            },
        }
        yield {"type": "progress", "step": "全部完成!", "progress": 1.0}

    except Exception as e:
        import traceback
        yield {"type": "error", "message": f"{e}\n{traceback.format_exc()}"}


def _write_jsonl(samples: list, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def _write_json(samples: list, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
