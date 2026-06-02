<script setup>
import { useRouter, useRoute } from 'vue-router'
import { Database, GraduationCap, HelpCircle } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const navItems = [
  { path: '/process', icon: Database, title: '数据处理' },
  { path: '/train', icon: GraduationCap, title: '训练' },
  { path: '/help', icon: HelpCircle, title: '帮助' },
]
</script>

<template>
  <aside class="w-[240px] flex flex-col shrink-0 overflow-y-auto border-r"
         style="background: var(--bg-sidebar); border-color: var(--border-subtle);">
    <!-- Logo -->
    <div class="h-14 flex items-center px-5 border-b" style="border-color: var(--border-subtle);">
      <span class="text-[15px] font-semibold tracking-tight">
        <span style="color: var(--accent);">cvat</span>
        <span style="color: var(--text-tertiary);">2</span>
        <span style="color: var(--accent);">qwen3vl</span>
      </span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 py-3 px-3">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 rounded-lg text-[13px] mb-1 transition-colors"
        :class="route.path === item.path ? 'font-medium' : ''"
        :style="{
          height: '40px',
          background: route.path === item.path ? 'var(--bg-input)' : 'transparent',
          color: route.path === item.path ? 'var(--text-primary)' : 'var(--text-secondary)',
        }"
      >
        <component :is="item.icon" :size="18" :stroke-width="1.8" />
        <span>{{ item.title }}</span>
      </router-link>
    </nav>

    <!-- Version -->
    <div class="px-5 py-4 text-xs" style="color: var(--text-tertiary);">
      v1.0.0
    </div>
  </aside>
</template>
