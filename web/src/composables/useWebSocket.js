import { ref, onUnmounted } from 'vue'
import { usePipelineStore } from '../stores/pipeline'

/**
 * WebSocket 连接管理
 * 用于 pipeline 实时进度推送
 */
export function useWebSocket() {
  const store = usePipelineStore()
  const ws = ref(null)
  const connected = ref(false)

  function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/pipeline`

    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
      store.addLog('已连接到服务器', 'info')
    }

    ws.value.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        store.handleEvent(event)

        // pipeline 完成或出错时标记停止
        if (event.type === 'result' || event.type === 'error') {
          store.isRunning = false
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err)
      }
    }

    ws.value.onclose = () => {
      connected.value = false
      store.addLog('连接已断开', 'info')
    }

    ws.value.onerror = (e) => {
      console.error('WebSocket error:', e)
      store.addLog('连接出错', 'error')
      connected.value = false
    }
  }

  function send(data) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    }
  }

  function startPipeline(inputPaths, outputDir = './output', config = {}) {
    store.reset()
    store.isRunning = true
    send({
      type: 'start',
      input_paths: inputPaths,
      output_dir: outputDir,
      config,
    })
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return { ws, connected, connect, send, startPipeline, disconnect }
}
