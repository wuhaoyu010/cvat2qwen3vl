<script setup>
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'
import { Cpu, Clock, Trash2, FolderOpen, X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: String, default: 'Qwen/Qwen3-VL-8B-Instruct' },
  showFamily: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'change'])

const grouped = ref({})
const flat = ref([])
const history = ref([])
const defaultModel = ref('Qwen/Qwen3-VL-8B-Instruct')
const selectedMeta = ref(null)
const showHistory = ref(false)
const newPath = ref('')

async function loadModels() {
  try {
    const resp = await axios.get('/api/models')
    grouped.value = resp.data.grouped
    flat.value = resp.data.flat
    defaultModel.value = resp.data.default
  } catch (e) {
    console.error('load models failed:', e)
  }
}

async function loadHistory() {
  try {
    const resp = await axios.get('/api/model-history')
    history.value = resp.data.history || []
  } catch (e) {
    history.value = []
  }
}

async function fetchMeta(path) {
  if (!path) return
  try {
    const resp = await axios.get(`/api/models/${encodeURIComponent(path)}`)
    selectedMeta.value = resp.data
  } catch (e) {
    selectedMeta.value = { name: path, family: 'custom', patch_size: 16, coord_range: 1000 }
  }
}

function onSelect(name) {
  emit('update:modelValue', name)
  emit('change', name)
  fetchMeta(name)
}

function useCustom() {
  if (!newPath.value.trim()) return
  onSelect(newPath.value.trim())
  newPath.value = ''
  showHistory.value = false
}

async function clearHistory() {
  if (!confirm('确认清空历史?')) return
  await axios.delete('/api/model-history')
  history.value = []
}

onMounted(() => {
  loadModels()
  loadHistory()
  if (props.modelValue) fetchMeta(props.modelValue)
})

watch(() => props.modelValue, (v) => {
  if (v) fetchMeta(v)
})
</script>

<template>
  <div class="space-y-3">
    <!-- Model selector -->
    <div class="form-group">
      <label class="form-label">模型选择</label>
      <select
        :value="modelValue"
        @change="onSelect($event.target.value)"
        class="select"
      >
        <optgroup
          v-for="(names, family) in grouped"
          :key="family"
          :label="family.toUpperCase()"
        >
          <option v-for="name in names" :key="name" :value="name">
            {{ name }}
          </option>
        </optgroup>
      </select>
    </div>

    <!-- Model meta -->
    <div v-if="selectedMeta" class="flex flex-wrap gap-2">
      <span v-if="selectedMeta.family" class="badge badge-accent">
        <Cpu :size="10" :stroke-width="2" />
        {{ selectedMeta.family }}
      </span>
      <span v-if="selectedMeta.hf_id" class="badge badge-info">
        {{ selectedMeta.hf_id }}
      </span>
      <span v-if="selectedMeta.patch_size" class="badge badge-info">
        patch {{ selectedMeta.patch_size }}
      </span>
      <span v-if="selectedMeta.coord_range" class="badge badge-accent">
        bbox 0-{{ selectedMeta.coord_range }}
      </span>
    </div>

    <!-- Custom path / history toggle -->
    <button
      type="button"
      class="btn-ghost text-xs"
      @click="showHistory = !showHistory"
    >
      <FolderOpen :size="14" :stroke-width="2" />
      {{ showHistory ? '收起' : '自定义路径 / 历史' }}
      <span v-if="history.length" class="badge badge-accent ml-1">{{ history.length }}</span>
    </button>

    <!-- Custom path panel -->
    <div v-if="showHistory" class="card space-y-3" style="padding: var(--space-4); background: var(--bg-empty);">
      <div class="flex gap-2">
        <input
          v-model="newPath"
          type="text"
          class="input flex-1"
          placeholder="本地路径或 HF ID，如 /path/to/model"
          @keyup.enter="useCustom"
        />
        <button
          type="button"
          class="btn-primary px-4"
          :disabled="!newPath.trim()"
          @click="useCustom"
        >
          使用
        </button>
      </div>

      <!-- History list -->
      <div v-if="history.length" class="space-y-1">
        <div class="flex justify-between items-center">
          <span class="text-xs font-medium" style="color: var(--text-secondary);">最近使用</span>
          <button class="btn-ghost text-xs" style="color: var(--danger);" @click="clearHistory">
            <Trash2 :size="12" :stroke-width="2" />
            清空
          </button>
        </div>
        <div
          v-for="h in history"
          :key="h.path"
          class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors"
          style="background: var(--bg-card);"
          @click="onSelect(h.path)"
          @mouseenter="$event.currentTarget.style.background = 'var(--bg-card-hover)'"
          @mouseleave="$event.currentTarget.style.background = 'var(--bg-card)'"
        >
          <Clock :size="12" :stroke-width="2" style="color: var(--text-tertiary); flex-shrink: 0;" />
          <span class="text-sm truncate flex-1" style="color: var(--text-primary);">{{ h.path }}</span>
          <span v-if="h.note" class="text-xs" style="color: var(--text-tertiary);">{{ h.note }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
