<script setup>
import { ref } from 'vue'
import { Upload, FileArchive, CheckCircle2, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  uploadedFiles: { type: Array, default: () => [] },
  uploading: { type: Boolean, default: false },
})

const emit = defineEmits(['upload'])
const dragOver = ref(false)
const fileInput = ref(null)

function handleDrop(e) {
  e.preventDefault()
  dragOver.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.zip'))
  if (files.length) emit('upload', files)
}

function handleSelect(e) {
  const files = Array.from(e.target.files)
  if (files.length) emit('upload', files)
}

function triggerSelect() {
  fileInput.value.click()
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="card-header-icon">
        <Upload :size="16" :stroke-width="2" />
      </div>
      <div>
        <div class="card-header-text">上传 ZIP 数据集</div>
        <div class="card-header-sub">包含 images/ 和 annotations.xml 的压缩包</div>
      </div>
    </div>

    <!-- Drop zone -->
    <div
      class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all"
      :class="dragOver ? 'border-[var(--accent)]' : ''"
      :style="{
        borderColor: dragOver ? 'var(--accent)' : 'var(--border)',
        background: dragOver ? 'var(--accent-soft)' : 'var(--bg-empty)',
        minHeight: '120px',
      }"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop="handleDrop"
      @click="triggerSelect"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".zip"
        class="hidden"
        @change="handleSelect"
      />

      <div v-if="uploading" class="flex flex-col items-center gap-2">
        <Loader2 :size="28" :stroke-width="1.5" class="animate-spin" style="color: var(--accent);" />
        <span class="text-sm" style="color: var(--text-secondary);">上传中...</span>
      </div>
      <div v-else class="flex flex-col items-center gap-2">
        <div class="empty-state-icon">
          <FileArchive :size="22" :stroke-width="1.5" />
        </div>
        <div class="text-sm" style="color: var(--text-secondary);">
          拖拽 ZIP 文件到此处，或
          <span class="font-medium" style="color: var(--accent);">点击选择</span>
        </div>
        <div class="text-xs" style="color: var(--text-tertiary);">支持 .zip 格式</div>
      </div>
    </div>

    <!-- Uploaded file list -->
    <div v-if="uploadedFiles.length" class="mt-4 space-y-2">
      <div
        v-for="(file, i) in uploadedFiles"
        :key="i"
        class="flex items-center gap-3 px-3 py-2 rounded-lg"
        style="background: var(--bg-empty);"
      >
        <CheckCircle2 :size="16" :stroke-width="2" style="color: var(--success);" />
        <span class="text-sm truncate flex-1" style="color: var(--text-primary);">{{ file.name }}</span>
        <span class="text-xs" style="color: var(--text-tertiary);">{{ (file.size / 1024 / 1024).toFixed(1) }} MB</span>
      </div>
    </div>
  </div>
</template>
