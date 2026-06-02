#!/bin/bash
# ==========================================
# ms-swift 训练脚本
# Qwen3-VL-8B-Instruct + LoRA微调
# ==========================================
#
# 前置要求:
#   1. 安装ms-swift: pip install ms-swift
#   2. 运行cvat2qwen3vl生成数据: python main.py
#   3. GPU显存 >= 24GB (推荐A100/H100)
#
# 使用方法:
#   bash scripts/train_swift.sh
#
# 参数说明 (可在下方修改):
#   MODEL_PATH: 模型路径 (本地路径或HuggingFace模型ID)
#   DATASET_PATH: main.py生成的train.jsonl路径
#   OUTPUT_DIR: 训练输出目录

set -e

# ============ 可修改参数 ============
MODEL_PATH="${MODEL_PATH:-Qwen/Qwen3-VL-8B-Instruct}"
DATASET_PATH="${DATASET_PATH:-./output/swift/train.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-./output/swift/checkpoints}"
VAL_DATASET="${VAL_DATASET:-./output/swift/val.jsonl}"

# LoRA参数
LORA_RANK="${LORA_RANK:-16}"
LORA_ALPHA="${LORA_ALPHA:-32}"
LORA_DROPOUT="${LORA_DROPOUT:-0.05}"

# 训练超参
BATCH_SIZE="${BATCH_SIZE:-2}"
GRAD_ACCUM="${GRAD_ACCUM:-8}"
LR="${LR:-1e-4}"
MAX_LENGTH="${MAX_LENGTH:-2048}"
EPOCHS="${EPOCHS:-3}"
SAVE_STEPS="${SAVE_STEPS:-500}"
LOG_STEPS="${LOG_STEPS:-50}"

# GPU配置
NUM_GPUS="${NUM_GPUS:-1}"
DEEPSPEED="${DEEPSPEED:-zero2}"
# ====================================

echo "=========================================="
echo "  ms-swift Qwen3-VL LoRA 训练"
echo "=========================================="
echo "模型:       ${MODEL_PATH}"
echo "数据集:     ${DATASET_PATH}"
echo "输出目录:   ${OUTPUT_DIR}"
echo "LoRA rank:  ${LORA_RANK}"
echo "DeepSpeed:  ${DEEPSPEED}"
echo "GPU数量:    ${NUM_GPUS}"
echo "=========================================="

# 检查数据集是否存在
if [ ! -f "${DATASET_PATH}" ]; then
    echo "[ERROR] 数据集不存在: ${DATASET_PATH}"
    echo "请先运行: python main.py"
    exit 1
fi

# 构建训练命令
# 参考: https://github.com/modelscope/ms-swift/blob/main/docs/source_en/Instruction/Command-line_training.md
TRAIN_CMD=(
    swift sft
    --model "${MODEL_PATH}"
    --dataset "${DATASET_PATH}"
    --output_dir "${OUTPUT_DIR}"

    # LoRA配置
    --tuner_type lora
    --lora_rank "${LORA_RANK}"
    --lora_alpha "${LORA_ALPHA}"
    --lora_dropout "${LORA_DROPOUT}"
    --target_modules ALL

    # 冻结视觉编码器 (Qwen3-VL训练时必须冻结ViT, 避免灾难性遗忘)
    --freeze_vit true

    # 数据处理
    --packing true
    --padding_free true
    --max_length "${MAX_LENGTH}"
    --truncation_strategy delete

    # 训练超参
    --num_train_epochs "${EPOCHS}"
    --per_device_train_batch_size "${BATCH_SIZE}"
    --gradient_accumulation_steps "${GRAD_ACCUM}"
    --learning_rate "${LR}"
    --lr_scheduler_type cosine
    --warmup_ratio 0.05
    --weight_decay 0.01
    --gradient_checkpointing true

    # 日志与保存
    --logging_steps "${LOG_STEPS}"
    --save_steps "${SAVE_STEPS}"
    --save_total_limit 3

    # 混合精度
    --torch_dtype bfloat16
    --attn_implementation flash_attention_2
)

# 验证集
if [ -f "${VAL_DATASET}" ]; then
    TRAIN_CMD+=(--val_dataset "${VAL_DATASET}")
fi

# DeepSpeed配置
if [ "${NUM_GPUS}" -gt 1 ]; then
    TRAIN_CMD+=(--deepspeed "${DEEPSPEED}")
fi

echo ""
echo "执行命令:"
echo "${TRAIN_CMD[*]}"
echo ""

# 执行训练
"${TRAIN_CMD[@]}"

echo ""
echo "=========================================="
echo "  训练完成!"
echo "  输出目录: ${OUTPUT_DIR}"
echo "=========================================="
