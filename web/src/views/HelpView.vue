<script setup>
import { Upload, Settings, Play, Download, GraduationCap, Box, Map, Tag, MousePointer2, FileText, Terminal } from 'lucide-vue-next'
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
    <!-- Quick start -->
    <div class="card lg:col-span-2">
      <div class="card-header">
        <div class="card-header-icon">
          <Play :size="16" :stroke-width="2" />
        </div>
        <div class="card-header-text">使用说明</div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 text-sm" style="color: var(--text-secondary); line-height: 1.8;">
        <div class="flex gap-3">
          <div class="flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5"
               style="background: var(--accent-soft); color: var(--accent);">
            <Upload :size="14" :stroke-width="2" />
          </div>
          <div>
            <div class="font-medium mb-1" style="color: var(--text-primary);">1. 上传</div>
            <p>拖入包含 images/ 和 annotations.xml 的 ZIP 文件</p>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5"
               style="background: var(--accent-soft); color: var(--accent);">
            <Settings :size="14" :stroke-width="2" />
          </div>
          <div>
            <div class="font-medium mb-1" style="color: var(--text-primary);">2. 配置</div>
            <p>调整训练集占比、任务开关等参数</p>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5"
               style="background: var(--accent-soft); color: var(--accent);">
            <Play :size="14" :stroke-width="2" />
          </div>
          <div>
            <div class="font-medium mb-1" style="color: var(--text-primary);">3. 生成</div>
            <p>自动执行解压、解析、验证、生成 QA</p>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5"
               style="background: var(--accent-soft); color: var(--accent);">
            <Download :size="14" :stroke-width="2" />
          </div>
          <div>
            <div class="font-medium mb-1" style="color: var(--text-primary);">4. 下载</div>
            <p>获取 Swift/Unsloth 格式训练文件</p>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5"
               style="background: var(--accent-soft); color: var(--accent);">
            <GraduationCap :size="14" :stroke-width="2" />
          </div>
          <div>
            <div class="font-medium mb-1" style="color: var(--text-primary);">5. 训练</div>
            <p>配置模型和超参，一键启动微调</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ZIP structure -->
    <div class="card">
      <div class="card-header">
        <div class="card-header-icon">
          <FileText :size="16" :stroke-width="2" />
        </div>
        <div class="card-header-text">ZIP 文件结构</div>
      </div>
      <pre class="text-sm p-4 rounded-lg leading-relaxed" style="background: var(--bg-code); color: var(--text-secondary); font-family: 'Cascadia Code', 'Fira Code', monospace;">dataset.zip
+-- images/
|   +-- img001.jpg
|   +-- img002.jpg
+-- annotations.xml</pre>
    </div>

    <!-- Annotation types -->
    <div class="card">
      <div class="card-header">
        <div class="card-header-icon">
          <Box :size="16" :stroke-width="2" />
        </div>
        <div class="card-header-text">支持的标注类型</div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-empty);">
          <Box :size="14" :stroke-width="2" style="color: var(--accent);" />
          <div>
            <div class="text-sm font-medium" style="color: var(--text-primary);">box</div>
            <div class="text-xs" style="color: var(--text-tertiary);">边界框</div>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-empty);">
          <Map :size="14" :stroke-width="2" style="color: var(--accent);" />
          <div>
            <div class="text-sm font-medium" style="color: var(--text-primary);">polygon</div>
            <div class="text-xs" style="color: var(--text-tertiary);">多边形 (自动转 bbox)</div>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-empty);">
          <Tag :size="14" :stroke-width="2" style="color: var(--accent);" />
          <div>
            <div class="text-sm font-medium" style="color: var(--text-primary);">tag</div>
            <div class="text-xs" style="color: var(--text-tertiary);">标签</div>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-empty);">
          <MousePointer2 :size="14" :stroke-width="2" style="color: var(--accent);" />
          <div>
            <div class="text-sm font-medium" style="color: var(--text-primary);">points</div>
            <div class="text-xs" style="color: var(--text-tertiary);">关键点</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Output format -->
    <div class="card">
      <div class="card-header">
        <div class="card-header-icon">
          <Download :size="16" :stroke-width="2" />
        </div>
        <div class="card-header-text">输出格式</div>
      </div>
      <div class="space-y-3 text-sm" style="color: var(--text-secondary);">
        <div class="p-3 rounded-lg" style="background: var(--bg-empty);">
          <strong style="color: var(--text-primary);">Swift:</strong> JSONL 格式，bbox 为绝对像素坐标（ms-swift 自动归一化到 0-1000）
        </div>
        <div class="p-3 rounded-lg" style="background: var(--bg-empty);">
          <strong style="color: var(--text-primary);">Unsloth:</strong> JSON 格式，bbox 已手动归一化到 0-1000
        </div>
      </div>
    </div>

    <!-- CLI usage -->
    <div class="card">
      <div class="card-header">
        <div class="card-header-icon">
          <Terminal :size="16" :stroke-width="2" />
        </div>
        <div class="card-header-text">命令行使用</div>
      </div>
      <pre class="text-sm p-4 rounded-lg leading-relaxed" style="background: var(--bg-code); color: var(--text-secondary); font-family: 'Cascadia Code', 'Fira Code', monospace;"># 数据处理 (CLI)
python main.py --config config.yaml

# 启动 Web UI
cd cvat2qwen3vl
uvicorn server.main:app --reload --port 8001
# 另一个终端
cd web && pnpm dev</pre>
    </div>
  </div>
</template>
