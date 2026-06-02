# cvat2qwen3vl

> CVAT 标注数据 → Qwen-VL 微调数据 一键转换工具

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

将 CVAT 导出的 ZIP 标注文件自动转换为 [ms-swift](https://github.com/modelscope/ms-swift) 和 [Unsloth](https://github.com/unslothai/unsloth) 可直接使用的微调数据格式，支持 Qwen2.5-VL / Qwen3-VL / Qwen3.5-VL / Qwen3.6-VL 全系列模型。

---

## ✨ Features

- **全标注类型支持** — box、polygon、tag、points、mask、skeleton、OCR
- **双任务生成** — Grounding（定位+描述）+ Verification（框内物体验证）
- **19 款模型** — 内置 Qwen2.5-VL / 3-VL / 3.5-VL / 3.6-VL 元数据，新增模型仅需改一行
- **双框架输出** — 同时生成 ms-swift JSONL 和 Unsloth JSON
- **Web UI** — 拖拽上传、实时日志、一键生成、一键下载、一键启动训练
- **CLI 模式** — `python main.py --config config.yaml` 命令行批量处理
- **跨平台** — Windows / Linux / macOS 一键启动脚本

---

## 🚀 Quick Start

### 首次安装

```bash
# 克隆仓库
git clone https://github.com/wuhaoyu010/cvat2qwen3vl.git
cd cvat2qwen3vl

# Windows 双击 setup.bat
# Linux / macOS
chmod +x setup.sh && ./setup.sh
```

### 启动

| 模式 | Windows | Linux / macOS |
|------|---------|---------------|
| 开发模式 | 双击 `start.bat` | `./start.sh` |
| 生产模式 | 双击 `start-prod.bat` | `./start-prod.sh` |

| 模式 | 地址 |
|------|------|
| 开发模式 | 前端 `http://localhost:5173` → 代理后端 `:8001` |
| 生产模式 | 直接访问 `http://localhost:8001` |

---

## 📖 Usage

### Web UI

1. **上传** — 拖入包含 `images/` + `annotations.xml` 的 ZIP 文件
2. **选模型** — 选择目标模型（决定 bbox 归一化范围）
3. **配参数** — 训练集占比、任务开关、负例比例等
4. **一键生成** — 自动执行：解压 → 解析 → 验证 → 生成 QA → 划分 → 输出
5. **下载** — 获取 Swift / Unsloth 格式训练文件
6. **启动训练** — 配置模型和超参，一键启动微调

### CLI

```bash
# 编辑配置
vim config.yaml

# 运行
python main.py --config config.yaml
```

---

## ⚙️ Configuration

`config.yaml` 示例：

```yaml
input_paths:
  - "../dataset1.zip"
  - "../dataset2.zip"

output_dir: "./output"

split_ratio:
  train: 0.9
  val: 0.1
  seed: 42

tasks:
  grounding: true        # Task 1: 定位+描述
  verification: true     # Task 2: 框内物体验证
  neg_sample_ratio: 0.3  # 负例样本占比

frameworks:
  - swift
  - unsloth
```

---

## 🤖 Supported Models

| Family | Models | Patch Size | Coord Range |
|--------|--------|------------|-------------|
| Qwen2.5-VL | 3B / 7B / 32B / 72B-Instruct | 14 | 0-1000 |
| Qwen3-VL | 2B / 4B / 8B / 32B-Instruct, 30B-A3B / 235B-A22B-Instruct | 16 | 0-1000 |
| Qwen3.5-VL | 2B / 4B / 9B / 27B / 35B-A3B / 122B-A10B / 397B-A17B | 16 | 0-1000 |
| Qwen3.6-VL | 27B / 35B-A3B | 16 | 0-1000 |

> 所有 Qwen2.5-VL+ 模型统一使用 0-1000 bbox 归一化范围。新增模型只需在 `model_registry.py` 添加条目。

---

## 📂 Project Structure

```
cvat2qwen3vl/
├── main.py                 # CLI 入口
├── config.yaml             # 默认配置
├── model_registry.py       # 模型注册表 (19 款)
├── requirements.txt        # Python 依赖
├── pyproject.toml          # 项目元数据
│
├── parsers/
│   └── cvat_parser.py      # CVAT XML 解析器
├── converters/
│   ├── coord_converter.py  # 坐标转换 (绝对 ↔ 归一化)
│   └── qa_generator.py     # QA 对生成器
├── pipeline/
│   ├── extract.py          # ZIP 解压 & 多数据集合并
│   ├── validate.py         # 数据验证
│   └── splitter.py         # 训练集/验证集划分
├── utils/
│   └── image_utils.py      # 图片工具函数
│
├── server/                 # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── api.py              # REST API
│   ├── ws.py               # WebSocket 实时推送
│   └── pipeline_runner.py  # Pipeline 异步执行器
│
├── web/                    # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── composables/    # WebSocket 组合式函数
│   │   └── assets/         # 样式和静态资源
│   └── package.json
│
├── scripts/
│   ├── train_swift.sh      # ms-swift 训练脚本
│   └── train_unsloth.py    # Unsloth 训练脚本
│
├── start.bat / start.sh            # 开发模式启动
├── start-prod.bat / start-prod.sh  # 生产模式启动
└── setup.bat / setup.sh            # 首次安装
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicor, WebSocket |
| Frontend | Vue 3, Pinia, Vue Router, Tailwind CSS v4, Lucide Icons |
| Build | Vite 8, pnpm |
| Training | ms-swift, Unsloth, PyTorch, Transformers |

---

## 📤 Output Formats

### Swift (ms-swift)

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": [
      {"type": "image", "image": "path/to/img.jpg"},
      {"type": "text", "text": "请描述图片中的内容，并用边界框标出所有目标。"}
    ]},
    {"role": "assistant", "content": "图片中包含以下目标：\n1. 「car」位于 [120,200,450,380]..."}
  ],
  "images": ["path/to/img.jpg"],
  "objects": {
    "ref": ["car", "person"],
    "bbox": [[120,200,450,380], [500,100,680,400]]
  }
}
```

> ms-swift 会在训练时自动将 bbox 归一化到 0-1000。

### Unsloth

```json
{
  "messages": [
    {"role": "user", "content": [
      {"type": "image", "image": "<PIL.Image>"},
      {"type": "text", "text": "请描述图片中的内容..."}
    ]},
    {"role": "assistant", "content": [
      {"type": "text", "text": "图片中包含以下目标：\n1. 「car」位于 [267,286,1000,543]..."}
    ]}
  ]
}
```

> Unsloth 格式中 bbox 已手动归一化到 0-1000。

---

## 🤝 Contributing

1. Fork 本仓库
2. 创建特性分支 `git checkout -b feature/amazing-feature`
3. 提交更改 `git commit -m 'feat: add amazing feature'`
4. 推送分支 `git push origin feature/amazing-feature`
5. 创建 Pull Request

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [ms-swift](https://github.com/modelscope/ms-swift) — 阿里通义千问微调框架
- [Unsloth](https://github.com/unslothai/unsloth) — 高效微调框架
- [CVAT](https://github.com/cvat-ai/cvat) — 计算机视觉标注工具
- [Qwen-VL](https://github.com/QwenLM/Qwen2-VL) — 通义千问视觉语言模型
