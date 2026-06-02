import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/process',
  },
  {
    path: '/process',
    name: 'Process',
    component: () => import('../views/ProcessView.vue'),
    meta: { title: '数据处理' },
  },
  {
    path: '/train',
    name: 'Train',
    component: () => import('../views/TrainView.vue'),
    meta: { title: '训练' },
  },
  {
    path: '/help',
    name: 'Help',
    component: () => import('../views/HelpView.vue'),
    meta: { title: '帮助' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
