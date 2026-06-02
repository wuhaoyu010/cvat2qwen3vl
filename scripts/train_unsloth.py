"""
Unsloth 训练脚本
=================
Qwen3-VL-8B-Instruct + LoRA微调 (4bit量化, 极速训练)

前置要求:
    1. pip install unsloth trl peft
    2. 运行cvat2qwen3vl生成数据: python main.py
    3. GPU显存 >= 12GB (推荐A100/H100)
    4. CUDA 12.1+

使用方法:
    python scripts/train_unsloth.py

环境变量:
    UNSLOTH_MODEL_PATH: 模型路径 (默认 Qwen/Qwen3-VL-8B-Instruct)
    UNSLOTH_OUTPUT_DIR: 输出目录
"""

import os
import sys
import json
import argparse
from pathlib import Path

# ============ 可修改参数 ============
MODEL_PATH = os.environ.get(
    "UNSLOTH_MODEL_PATH", "Qwen/Qwen3-VL-8B-Instruct"
)
OUTPUT_DIR = os.environ.get(
    "UNSLOTH_OUTPUT_DIR", "./output/unsloth/checkpoints"
)
TRAIN_DATA = os.environ.get(
    "UNSLOTH_TRAIN_DATA", "./output/unsloth/train.json"
)
VAL_DATA = os.environ.get(
    "UNSLOTH_VAL_DATA", "./output/unsloth/val.json"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Unsloth Qwen-VL LoRA training")
    parser.add_argument("--model_name", type=str, default=None,
                        help="Model path or HuggingFace ID")
    parser.add_argument("--train_file", type=str, default=None,
                        help="Training data JSON path")
    parser.add_argument("--val_file", type=str, default=None,
                        help="Validation data JSON path")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--num_epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--lora_rank", type=int, default=None)
    parser.add_argument("--max_seq_len", type=int, default=None)
    args = parser.parse_args()
    # CLI args override env vars / defaults
    global MODEL_PATH, TRAIN_DATA, VAL_DATA, OUTPUT_DIR
    if args.model_name:
        MODEL_PATH = args.model_name
    if args.train_file:
        TRAIN_DATA = args.train_file
    if args.val_file:
        VAL_DATA = args.val_file
    if args.output_dir:
        OUTPUT_DIR = args.output_dir
    return args

# 训练超参
NUM_EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM = 8
LR = 2e-4
MAX_SEQ_LEN = 2048
SAVE_STEPS = 500
LOG_STEPS = 50

# LoRA参数
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
# ====================================

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image


def load_dataset_from_json(json_path: str):
    """
    从Unsloth格式的JSON文件加载数据集
    
    参数:
        json_path: JSON文件路径, 内容为sample列表
        
    返回:
        datasets.Dataset
    """
    from datasets import Dataset
    
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Unsloth格式: 每个sample的messages中包含PIL Image对象
    # 这里从文件路径加载PIL Image
    processed = []
    for item in raw_data:
        messages = item.get("messages", [])
        new_messages = []
        
        for msg in messages:
            content = msg.get("content", [])
            new_content = []
            
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict):
                        if c.get("type") == "image":
                            # 从路径加载图片为PIL Image
                            img_path = c.get("image", "")
                            if isinstance(img_path, str) and Path(img_path).exists():
                                pil_img = Image.open(img_path).convert("RGB")
                                new_content.append({
                                    "type": "image",
                                    "image": pil_img,
                                })
                            else:
                                # 如果已经是PIL Image, 直接使用
                                new_content.append(c)
                        else:
                            new_content.append(c)
                    else:
                        new_content.append(c)
            else:
                new_content = content
            
            new_messages.append({
                "role": msg.get("role", ""),
                "content": new_content,
            })
        
        processed.append({"messages": new_messages})
    
    return Dataset.from_list(processed)


def format_data_for_unsloth(data):
    """
    Unsloth格式化: 将messages转换为训练格式
    
    Unsloth官方格式:
        {"messages": [{"role": "user", "content": [...]},
                       {"role": "assistant", "content": [...]}]}
    
    内容列表支持:
        {"type": "text", "text": "..."}
        {"type": "image", "image": PIL.Image}
    """
    formatted = []
    for item in data:
        formatted.append({
            "messages": item["messages"]
        })
    return formatted





def main():
    """主训练流程"""
    parse_args()
    
    print("=" * 60)
    print("  Unsloth Qwen3-VL LoRA 训练")
    print("=" * 60)
    print(f"模型:       {MODEL_PATH}")
    print(f"训练数据:   {TRAIN_DATA}")
    print(f"输出目录:   {OUTPUT_DIR}")
    print(f"LoRA rank:  {LORA_R}")
    print(f"4bit量化:   启用")
    print("=" * 60)
    
    # 检查数据
    if not Path(TRAIN_DATA).exists():
        print(f"[ERROR] 训练数据不存在: {TRAIN_DATA}")
        print("请先运行: python main.py")
        sys.exit(1)
    
    # ==================== 1. 加载模型 ====================
    print("\n[1/4] 加载模型 (4bit量化)...")
    
    from unsloth import FastVisionModel
    
    model, tokenizer = FastVisionModel.from_pretrained(
        model_name=MODEL_PATH,
        load_in_4bit=True,
        use_gradient_checkpointing="unsloth",  # Unsloth优化
    )
    
    # ==================== 2. 配置LoRA ====================
    print("\n[2/4] 配置LoRA...")
    
    model = FastVisionModel.get_peft_model(
        model,
        finetune_vision_layers=False,      # 冻结视觉编码器 (Qwen3-VL推荐)
        finetune_language_layers=True,      # 微调语言模型
        finetune_attention_modules=True,    # 微调注意力层
        finetune_mlp_modules=True,          # 微调MLP层
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )
    
    # ==================== 3. 加载数据 ====================
    print("\n[3/4] 加载数据...")
    
    from unsloth.trainer import UnslothVisionDataCollator
    from trl import SFTTrainer, SFTConfig
    
    train_dataset = load_dataset_from_json(TRAIN_DATA)
    print(f"  训练样本数: {len(train_dataset)}")
    
    val_dataset = None
    if Path(VAL_DATA).exists():
        val_dataset = load_dataset_from_json(VAL_DATA)
        print(f"  验证样本数: {len(val_dataset)}")
    
    # ==================== 4. 训练 ====================
    print("\n[4/4] 开始训练...")
    
    FastVisionModel.for_training(model)
    
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    training_args = SFTConfig(
        output_dir=str(output_path),
        
        # 训练超参
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        weight_decay=0.01,
        
        # 精度与优化
        fp16=False,
        bf16=True,                         # Qwen3-VL推荐bf16
        optim="adamw_8bit",
        max_seq_length=MAX_SEQ_LEN,
        logging_steps=LOG_STEPS,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        
        # Unsloth必须配置
        remove_unused_columns=False,
        dataset_text_field="",
        dataset_kwargs={"skip_prepare_dataset": True},
        
        # 分布式训练
        report_to="none",
    )
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=UnslothVisionDataCollator(model, tokenizer),
        args=training_args,
    )
    
    # 开始训练
    trainer_stats = trainer.train()
    
    print("\n" + "=" * 60)
    print("  训练完成!")
    print(f"  训练loss: {trainer_stats.training_loss:.4f}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 保存最终模型
    final_path = output_path / "final"
    model.save_pretrained(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    print(f"  模型保存: {final_path}")


if __name__ == "__main__":
    main()
