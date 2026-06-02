import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePipelineStore = defineStore('pipeline', () => {
  // 上传的文件路径 (服务器端路径)
  const uploadedPaths = ref([])

  // Pipeline 状态
  const isRunning = ref(false)
  const progress = ref(0)
  const currentStep = ref('')
  const logs = ref([])

  // 结果
  const stats = ref(null)
  const validation = ref(null)
  const outputFiles = ref({})
  const sampleCounts = ref({})
  const trainCounts = ref({})
  const valCounts = ref({})
  const samplePreview = ref(null)

  // 错误
  const error = ref('')

  function addLog(message, type = 'info') {
    logs.value.push({ message, type, time: new Date().toLocaleTimeString() })
  }

  function reset() {
    isRunning.value = false
    progress.value = 0
    currentStep.value = ''
    logs.value = []
    stats.value = null
    validation.value = null
    outputFiles.value = {}
    sampleCounts.value = {}
    trainCounts.value = {}
    valCounts.value = {}
    samplePreview.value = null
    error.value = ''
  }

  function handleEvent(event) {
    switch (event.type) {
      case 'progress':
        progress.value = event.progress
        currentStep.value = event.step
        break
      case 'log':
        addLog(event.message, 'info')
        break
      case 'result':
        stats.value = event.data.stats
        validation.value = event.data.validation
        outputFiles.value = event.data.output_files
        sampleCounts.value = event.data.sample_counts
        trainCounts.value = event.data.train_counts
        valCounts.value = event.data.val_counts
        samplePreview.value = event.data.sample_preview
        addLog('全部完成!', 'success')
        break
      case 'error':
        error.value = event.message
        addLog(event.message, 'error')
        break
    }
  }

  return {
    uploadedPaths,
    isRunning,
    progress,
    currentStep,
    logs,
    stats,
    validation,
    outputFiles,
    sampleCounts,
    trainCounts,
    valCounts,
    samplePreview,
    error,
    addLog,
    reset,
    handleEvent,
  }
})
