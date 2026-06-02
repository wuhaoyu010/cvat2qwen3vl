<script setup>
import { ref, onMounted } from 'vue'
import { usePipelineStore } from '../stores/pipeline'
import { useWebSocket } from '../composables/useWebSocket'
import { Play, Loader2, Target } from 'lucide-vue-next'
import FileUpload from '../components/FileUpload.vue'
import ConfigPanel from '../components/ConfigPanel.vue'
import ModelSelector from '../components/ModelSelector.vue'
import ProgressLog from '../components/ProgressLog.vue'
import StatsPanel from '../components/StatsPanel.vue'
import SamplePreview from '../components/SamplePreview.vue'
import DownloadPanel from '../components/DownloadPanel.vue'
import axios from 'axios'

const store = usePipelineStore()
const { connected, connect, startPipeline } = useWebSocket()

const config = ref({
  train_ratio: 0.9,
  seed: 42,
  grounding: true,
  verification: true,
  neg_sample_ratio: 0.3,
  frameworks: ['swift', 'unsloth'],
  fix_bbox: true,
  skip_empty: false,
})

const targetModel = ref('Qwen/Qwen3-VL-8B-Instruct')
const showModelPicker = ref(false)
const uploadedFiles = ref([])
const uploadedPaths = ref([])
const uploading = ref(false)

onMounted(() => {
  connect()
})

async function handleFileUpload(files) {
  uploading.value = true
  try {
    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }
    const resp = await axios.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    uploadedPaths.value = resp.data.paths
    uploadedFiles.value = files
    store.addLog(`上传完成: ${resp.data.count} 个文件`, 'success')
  } catch (e) {
    store.addLog(`上传失败: ${e.message}`, 'error')
  } finally {
    uploading.value = false
  }
}

function handleRun() {
  if (!uploadedPaths.value.length) {
    store.addLog('请先上传 ZIP 文件', 'error')
    return
  }

  const pipelineConfig = {
    split_ratio: {
      train: config.value.train_ratio,
      val: 1 - config.value.train_ratio,
      seed: config.value.seed,
      stratify_by_label: false,
    },
    tasks: {
      grounding: config.value.grounding,
      verification: config.value.verification,
      neg_sample_ratio: config.value.neg_sample_ratio,
    },
    frameworks: config.value.frameworks,
    validation: {
      fix_bbox_clipping: config.value.fix_bbox,
      skip_empty_annotations: config.value.skip_empty,
    },
    model_name: targetModel.value,
  }

  startPipeline(uploadedPaths.value, './output', pipelineConfig)
}

function handleDownload(filePath) {
  window.open(`/api/download?path=${encodeURIComponent(filePath)}`, '_blank')
}
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-5 h-full">
    <!-- Left: Config & Upload -->
    <div class="space-y-5 min-w-0">
      <FileUpload
        :uploaded-files="uploadedFiles"
        :uploading="uploading"
        @upload="handleFileUpload"
      />

      <!-- Target model -->
      <div class="card">
        <div class="card-header">
          <div class="card-header-icon">
            <Target :size="16" :stroke-width="2" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="card-header-text">目标模型</div>
            <div class="card-header-sub">决定 bbox 归一化范围</div>
          </div>
          <button
            class="btn-ghost text-xs shrink-0"
            @click="showModelPicker = !showModelPicker"
          >
            {{ showModelPicker ? '收起' : '展开' }}
          </button>
        </div>

        <div class="flex items-center gap-2 text-sm mb-2">
          <span style="color: var(--text-secondary);">当前:</span>
          <span class="badge badge-accent truncate">{{ targetModel }}</span>
        </div>
        <div class="text-xs" style="color: var(--text-tertiary);">
          所有 Qwen2.5-VL+ 模型 bbox 归一化范围均为 0-1000
        </div>

        <div v-if="showModelPicker" class="mt-4">
          <ModelSelector v-model="targetModel" />
        </div>
      </div>

      <ConfigPanel v-model="config" />

      <!-- Run button -->
      <button
        class="btn-primary w-full py-3 text-base font-medium"
        :disabled="store.isRunning || !uploadedPaths.length"
        @click="handleRun"
      >
        <template v-if="store.isRunning">
          <Loader2 :size="18" :stroke-width="2" class="animate-spin" />
          正在生成...
        </template>
        <template v-else>
          <Play :size="18" :stroke-width="2" />
          一键生成
        </template>
      </button>
    </div>

    <!-- Right: Results & Logs -->
    <div class="space-y-5 min-w-0">
      <!-- Progress bar -->
      <div v-if="store.isRunning || store.progress > 0" class="card" style="padding: var(--space-4);">
        <div class="flex justify-between items-center text-sm mb-2">
          <span style="color: var(--text-secondary);">{{ store.currentStep }}</span>
          <span class="badge badge-accent">{{ Math.round(store.progress * 100) }}%</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-bar-fill"
            :style="{ width: store.progress * 100 + '%' }"
          />
        </div>
      </div>

      <ProgressLog />

      <div v-if="store.stats" class="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <StatsPanel />
        <SamplePreview />
      </div>

      <DownloadPanel @download="handleDownload" />
    </div>
  </div>
</template>
