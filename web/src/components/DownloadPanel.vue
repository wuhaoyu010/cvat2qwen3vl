<script setup>
import { usePipelineStore } from '../stores/pipeline'
import { Download, FileText, FolderOpen } from 'lucide-vue-next'

const store = usePipelineStore()
const emit = defineEmits(['download'])
</script>

<template>
  <div v-if="Object.keys(store.outputFiles).length" class="card">
    <div class="card-header">
      <div class="card-header-icon">
        <Download :size="16" :stroke-width="2" />
      </div>
      <div class="card-header-text">下载训练文件</div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <button
        v-for="(info, key) in store.outputFiles"
        :key="key"
        class="btn-secondary text-left flex items-center gap-3 p-3"
        @click="emit('download', info.path)"
      >
        <FileText :size="18" :stroke-width="1.8" style="color: var(--accent); flex-shrink: 0;" />
        <div class="min-w-0 flex-1">
          <div class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ info.name || key }}</div>
          <div class="text-xs" style="color: var(--text-tertiary);">{{ info.framework || key.split('/')[0] }}</div>
        </div>
      </button>
    </div>
  </div>
</template>
