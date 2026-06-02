<script setup>
import { usePipelineStore } from '../stores/pipeline'
import { Eye } from 'lucide-vue-next'

const store = usePipelineStore()
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="card-header-icon">
        <Eye :size="16" :stroke-width="2" />
      </div>
      <div class="card-header-text">样本预览</div>
    </div>

    <div v-if="store.samplePreview" class="space-y-3">
      <!-- Image name -->
      <div v-if="store.samplePreview.images" class="flex items-center gap-2">
        <span class="badge badge-info">图片</span>
        <span class="text-sm truncate" style="color: var(--text-primary);">{{ store.samplePreview.images[0] }}</span>
      </div>

      <!-- Messages -->
      <div
        v-for="(msg, i) in store.samplePreview.messages"
        :key="i"
        class="rounded-lg p-3 text-xs"
        :style="{
          background: msg.role === 'user' ? 'var(--info-soft)' : 'var(--accent-soft)',
          borderLeft: msg.role === 'user' ? '3px solid var(--info)' : '3px solid var(--accent)',
        }"
      >
        <div class="font-semibold mb-1.5" :style="{ color: msg.role === 'user' ? 'var(--info)' : 'var(--accent)' }">
          {{ msg.role === 'user' ? 'User' : 'Assistant' }}
        </div>
        <div class="whitespace-pre-wrap break-all leading-relaxed" style="color: var(--text-secondary);">
          {{ typeof msg.content === 'string'
            ? (msg.content.length > 200 ? msg.content.slice(0, 200) + '...' : msg.content)
            : '[complex content]'
          }}
        </div>
      </div>

      <!-- Objects -->
      <div v-if="store.samplePreview.objects" class="flex flex-wrap gap-2">
        <span v-if="store.samplePreview.objects.ref" class="badge badge-info">
          refs: {{ store.samplePreview.objects.ref?.length }}
        </span>
        <span v-if="store.samplePreview.objects.bbox" class="badge badge-accent">
          bbox: {{ store.samplePreview.objects.bbox?.length }}
        </span>
      </div>
    </div>

    <div v-else class="empty-state" style="padding: var(--space-6);">
      <div class="empty-state-icon">
        <Eye :size="22" :stroke-width="1.5" />
      </div>
      <div class="empty-state-text">生成完成后预览 QA 样本</div>
    </div>
  </div>
</template>
