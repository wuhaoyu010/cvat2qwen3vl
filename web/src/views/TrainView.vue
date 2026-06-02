<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { GraduationCap, Play, Loader2, Terminal, CheckCircle2, AlertCircle } from 'lucide-vue-next'
import ModelSelector from '../components/ModelSelector.vue'

const framework = ref('swift')
const modelPath = ref('Qwen/Qwen3-VL-8B-Instruct')
const modelFamily = ref('qwen3-vl')
const epochs = ref(3)
const batchSize = ref(2)
const lr = ref(0.0001)
const loraRank = ref(16)

const launching = ref(false)
const logs = ref([])
const pid = ref(null)
const trainInfo = ref(null)

async function launchTraining() {
  launching.value = true
  logs.value = [{ text: '启动训练...', type: 'info' }]

  try {
    const resp = await axios.post('/api/launch-training', {
      framework: framework.value,
      model_path: modelPath.value,
      model_family: modelFamily.value,
      epochs: epochs.value,
      batch_size: batchSize.value,
      lr: lr.value,
      lora_rank: loraRank.value,
    })

    pid.value = resp.data.pid
    trainInfo.value = {
      trainFile: resp.data.train_file,
      modelPath: resp.data.model_path,
    }
    logs.value.push({ text: `训练已启动 (PID: ${resp.data.pid})`, type: 'success' })
    logs.value.push({ text: `训练数据: ${resp.data.train_file}`, type: 'info' })
    logs.value.push({ text: `模型: ${resp.data.model_path}`, type: 'info' })
    logs.value.push({ text: `命令: ${resp.data.command}`, type: 'info' })
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    logs.value.push({ text: `启动失败: ${msg}`, type: 'error' })
  } finally {
    launching.value = false
  }
}

function onModelChange(name) {
  modelPath.value = name
  if (name.startsWith('Qwen2.5')) modelFamily.value = 'qwen2.5-vl'
  else if (name.startsWith('Qwen3-VL')) modelFamily.value = 'qwen3-vl'
  else if (name.startsWith('Qwen3.5')) modelFamily.value = 'qwen3.5-vl'
  else if (name.startsWith('Qwen3.6')) modelFamily.value = 'qwen3.6-vl'
  else modelFamily.value = 'custom'
}
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-5 h-full">
    <!-- Left: Config -->
    <div class="space-y-5 min-w-0">
      <div class="card">
        <div class="card-header">
          <div class="card-header-icon">
            <GraduationCap :size="16" :stroke-width="2" />
          </div>
          <div class="card-header-text">微调训练</div>
        </div>

        <div class="space-y-5">
          <!-- Framework -->
          <div class="form-group">
            <label class="form-label">训练框架</label>
            <div class="flex gap-4">
              <label class="radio-wrap">
                <input type="radio" v-model="framework" value="swift" />
                <span class="radio-label">Swift (ms-swift)</span>
              </label>
              <label class="radio-wrap">
                <input type="radio" v-model="framework" value="unsloth" />
                <span class="radio-label">Unsloth (4bit 量化)</span>
              </label>
            </div>
          </div>

          <!-- Model selector -->
          <ModelSelector
            v-model="modelPath"
            @change="onModelChange"
          />

          <!-- Hyperparameters -->
          <div class="form-group">
            <label class="form-label">超参数配置</label>
            <div class="grid grid-cols-2 gap-4">
              <div class="form-group">
                <div class="flex justify-between items-center">
                  <span class="text-sm" style="color: var(--text-secondary);">训练轮数</span>
                  <span class="badge badge-accent">{{ epochs }}</span>
                </div>
                <input type="range" v-model.number="epochs" min="1" max="10" step="1" />
              </div>
              <div class="form-group">
                <div class="flex justify-between items-center">
                  <span class="text-sm" style="color: var(--text-secondary);">Batch Size</span>
                  <span class="badge badge-accent">{{ batchSize }}</span>
                </div>
                <input type="range" v-model.number="batchSize" min="1" max="8" step="1" />
              </div>
              <div class="form-group">
                <label class="form-label" for="lr">学习率</label>
                <input id="lr" v-model.number="lr" type="number" step="0.00001" class="input" />
              </div>
              <div class="form-group">
                <div class="flex justify-between items-center">
                  <span class="text-sm" style="color: var(--text-secondary);">LoRA Rank</span>
                  <span class="badge badge-accent">{{ loraRank }}</span>
                </div>
                <input type="range" v-model.number="loraRank" min="4" max="64" step="4" />
              </div>
            </div>
          </div>

          <!-- Launch button -->
          <button
            class="btn-primary w-full py-3 text-base font-medium"
            :disabled="launching"
            @click="launchTraining"
          >
            <template v-if="launching">
              <Loader2 :size="18" :stroke-width="2" class="animate-spin" />
              启动中...
            </template>
            <template v-else>
              <Play :size="18" :stroke-width="2" />
              启动训练
            </template>
          </button>
        </div>
      </div>
    </div>

    <!-- Right: Log -->
    <div class="space-y-5 min-w-0">
      <div class="card">
        <div class="card-header">
          <div class="card-header-icon">
            <Terminal :size="16" :stroke-width="2" />
          </div>
          <div class="card-header-text">训练日志</div>
        </div>

        <div class="log-box" style="min-height: 200px; max-height: 500px;">
          <div v-if="!logs.length" class="flex items-center justify-center h-full">
            <span class="text-sm" style="color: var(--text-tertiary);">等待启动...</span>
          </div>
          <div
            v-for="(log, i) in logs"
            :key="i"
            class="log-line"
            :class="log.type"
          >
            <span class="mr-1.5" v-if="log.type === 'success'">
              <CheckCircle2 :size="12" :stroke-width="2" style="vertical-align: -1px;" />
            </span>
            <span class="mr-1.5" v-else-if="log.type === 'error'">
              <AlertCircle :size="12" :stroke-width="2" style="vertical-align: -1px;" />
            </span>
            {{ log.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
