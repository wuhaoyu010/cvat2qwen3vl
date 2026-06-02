<script setup>
import { Settings, ChevronDown } from 'lucide-vue-next'

const model = defineModel()

function update(key, value) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="card-header-icon">
        <Settings :size="16" :stroke-width="2" />
      </div>
      <div class="card-header-text">参数配置</div>
    </div>

    <div class="space-y-5">
      <!-- Train ratio -->
      <div class="form-group">
        <div class="flex justify-between items-center">
          <label class="form-label">训练集占比</label>
          <span class="badge badge-accent">{{ model.train_ratio }}</span>
        </div>
        <input
          type="range"
          :value="model.train_ratio"
          min="0.5" max="0.95" step="0.05"
          @input="update('train_ratio', parseFloat($event.target.value))"
        />
        <div class="form-hint">建议 0.85 ~ 0.95，数据量充足时可适当调低</div>
      </div>

      <!-- Seed -->
      <div class="form-group">
        <label class="form-label" for="seed">随机种子</label>
        <input
          id="seed"
          type="number"
          class="input"
          :value="model.seed"
          @input="update('seed', parseInt($event.target.value) || 42)"
        />
        <div class="form-hint">固定种子可确保结果可复现</div>
      </div>

      <!-- Task toggles -->
      <div class="form-group">
        <label class="form-label">任务类型</label>
        <div class="space-y-1">
          <label class="checkbox-wrap">
            <input
              type="checkbox"
              :checked="model.grounding"
              @change="update('grounding', $event.target.checked)"
            />
            <span class="checkbox-label">Task 1: 定位 + 描述 (Grounding)</span>
          </label>
          <label class="checkbox-wrap">
            <input
              type="checkbox"
              :checked="model.verification"
              @change="update('verification', $event.target.checked)"
            />
            <span class="checkbox-label">Task 2: 框内物体验证</span>
          </label>
        </div>
      </div>

      <!-- Negative sample ratio -->
      <div class="form-group">
        <div class="flex justify-between items-center">
          <label class="form-label">负例样本占比</label>
          <span class="badge badge-accent">{{ model.neg_sample_ratio }}</span>
        </div>
        <input
          type="range"
          :value="model.neg_sample_ratio"
          min="0" max="0.5" step="0.05"
          @input="update('neg_sample_ratio', parseFloat($event.target.value))"
        />
        <div class="form-hint">仅用于 Task 2，随机替换标注标签生成负样本</div>
      </div>

      <!-- Framework output -->
      <div class="form-group">
        <label class="form-label">输出框架</label>
        <div class="space-y-1">
          <label class="checkbox-wrap">
            <input
              type="checkbox"
              :checked="model.frameworks.includes('swift')"
              @change="update('frameworks', $event.target.checked
                ? [...model.frameworks, 'swift']
                : model.frameworks.filter(f => f !== 'swift'))"
            />
            <span class="checkbox-label">Swift (ms-swift JSONL)</span>
          </label>
          <label class="checkbox-wrap">
            <input
              type="checkbox"
              :checked="model.frameworks.includes('unsloth')"
              @change="update('frameworks', $event.target.checked
                ? [...model.frameworks, 'unsloth']
                : model.frameworks.filter(f => f !== 'unsloth'))"
            />
            <span class="checkbox-label">Unsloth (JSON, bbox 已归一化)</span>
          </label>
        </div>
      </div>

      <!-- Advanced options -->
      <details class="group">
        <summary class="flex items-center gap-2 text-sm cursor-pointer select-none"
                 style="color: var(--text-secondary); min-height: var(--touch-min);">
          <ChevronDown :size="14" :stroke-width="2" class="transition-transform group-open:rotate-90" />
          高级选项
        </summary>
        <div class="mt-2 space-y-1 pl-6">
          <label class="checkbox-wrap">
            <input
              type="checkbox"
              :checked="model.fix_bbox"
              @change="update('fix_bbox', $event.target.checked)"
            />
            <span class="checkbox-label">自动修正超出范围的 bbox</span>
          </label>
          <label class="checkbox-wrap">
            <input
              type="checkbox"
              :checked="model.skip_empty"
              @change="update('skip_empty', $event.target.checked)"
            />
            <span class="checkbox-label">跳过无标注的图片</span>
          </label>
        </div>
      </details>
    </div>
  </div>
</template>
