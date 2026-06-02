<script setup>
import { usePipelineStore } from '../stores/pipeline'
import { BarChart3, TrendingUp, Hash, Layers } from 'lucide-vue-next'

const store = usePipelineStore()
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="card-header-icon">
        <BarChart3 :size="16" :stroke-width="2" />
      </div>
      <div class="card-header-text">统计信息</div>
    </div>

    <div v-if="store.stats" class="space-y-4">
      <!-- Overview numbers -->
      <div class="grid grid-cols-2 gap-3">
        <div class="p-3 rounded-lg" style="background: var(--bg-empty);">
          <div class="flex items-center gap-2 mb-1">
            <Layers :size="12" :stroke-width="2" style="color: var(--accent);" />
            <span class="text-xs" style="color: var(--text-secondary);">总图片数</span>
          </div>
          <div class="text-xl font-semibold" style="color: var(--text-primary);">{{ store.stats.total_images }}</div>
        </div>
        <div class="p-3 rounded-lg" style="background: var(--bg-empty);">
          <div class="flex items-center gap-2 mb-1">
            <Hash :size="12" :stroke-width="2" style="color: var(--accent);" />
            <span class="text-xs" style="color: var(--text-secondary);">总标注数</span>
          </div>
          <div class="text-xl font-semibold" style="color: var(--text-primary);">{{ store.stats.total_annotations }}</div>
        </div>
      </div>

      <!-- Label distribution -->
      <div v-if="store.stats.label_counts">
        <div class="flex items-center gap-2 mb-2">
          <TrendingUp :size="12" :stroke-width="2" style="color: var(--text-secondary);" />
          <span class="text-xs font-medium" style="color: var(--text-secondary);">类别分布</span>
        </div>
        <div class="space-y-2">
          <div
            v-for="(count, label) in store.stats.label_counts"
            :key="label"
            class="flex items-center gap-2"
          >
            <span class="text-sm truncate w-[100px]" style="color: var(--text-primary);">{{ label }}</span>
            <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background: var(--bg-input);">
              <div
                class="h-full rounded-full transition-all"
                :style="{
                  width: (count / store.stats.total_annotations * 100) + '%',
                  background: 'var(--accent)',
                }"
              />
            </div>
            <span class="text-xs w-8 text-right tabular-nums" style="color: var(--text-tertiary);">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- Validation -->
      <div v-if="store.validation" class="flex gap-2">
        <span class="badge badge-success">有效: {{ store.validation.valid }}</span>
        <span v-if="store.validation.invalid > 0" class="badge badge-danger">无效: {{ store.validation.invalid }}</span>
      </div>

      <!-- Sample counts -->
      <div v-if="Object.keys(store.sampleCounts).length" class="space-y-1">
        <div
          v-for="(count, fw) in store.sampleCounts"
          :key="fw"
          class="flex items-center gap-2 text-sm"
        >
          <span class="badge badge-info">{{ fw }}</span>
          <span style="color: var(--text-secondary);">
            {{ count }} 样本
            <span class="text-xs" style="color: var(--text-tertiary);">
              (train: {{ store.trainCounts[fw] }}, val: {{ store.valCounts[fw] }})
            </span>
          </span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state" style="padding: var(--space-6);">
      <div class="empty-state-icon">
        <BarChart3 :size="22" :stroke-width="1.5" />
      </div>
      <div class="empty-state-text">生成完成后显示统计信息</div>
    </div>
  </div>
</template>
