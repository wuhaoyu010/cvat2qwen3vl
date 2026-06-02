<script setup>
import { ref, watch, nextTick } from 'vue'
import { usePipelineStore } from '../stores/pipeline'
import { Terminal } from 'lucide-vue-next'

const store = usePipelineStore()
const logBox = ref(null)

watch(() => store.logs.length, async () => {
  await nextTick()
  if (logBox.value) {
    logBox.value.scrollTop = logBox.value.scrollHeight
  }
})

function logClass(type) {
  switch (type) {
    case 'success': return 'success'
    case 'error': return 'error'
    default: return ''
  }
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="card-header-icon">
        <Terminal :size="16" :stroke-width="2" />
      </div>
      <div class="card-header-text">执行日志</div>
    </div>

    <div ref="logBox" class="log-box" style="min-height: 160px; max-height: 240px;">
      <div v-if="!store.logs.length" class="flex items-center justify-center h-full">
        <span class="text-sm" style="color: var(--text-tertiary);">等待执行...</span>
      </div>
      <div
        v-for="(log, i) in store.logs"
        :key="i"
        class="log-line"
        :class="logClass(log.type)"
      >
        <span class="mr-2 text-xs" style="color: var(--text-tertiary);">{{ log.time }}</span>
        {{ log.message }}
      </div>
    </div>
  </div>
</template>
