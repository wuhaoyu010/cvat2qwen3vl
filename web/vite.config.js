import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import path from 'path'

function getBackendPort() {
  const portFile = path.resolve(__dirname, '../.backend_port')
  try {
    return parseInt(fs.readFileSync(portFile, 'utf-8').trim())
  } catch {
    return 8001
  }
}

const backendPort = getBackendPort()

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://localhost:${backendPort}`,
        ws: true,
      },
    },
  },
})
