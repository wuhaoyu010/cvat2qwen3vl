<script setup>
import Sidebar from './Sidebar.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <Sidebar />

    <div class="flex-1 flex flex-col overflow-hidden">
      <header class="h-14 border-b flex items-center px-6 shrink-0"
              style="border-color: var(--border-subtle); background: var(--bg-main);">
        <span class="text-base font-semibold" style="color: var(--text-primary);">{{ route.meta.title }}</span>
      </header>

      <main class="flex-1 overflow-y-auto">
        <div class="p-6 max-w-[1400px]">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
