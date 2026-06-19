import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    { path: '/', redirect: '/projects' },
    { path: '/projects', name: 'projects', component: () => import('@/views/Projects.vue') },
    {
      path: '/project/:id',
      component: () => import('@/views/ProjectDetail.vue'),
      children: [
        { path: '', redirect: 'iterations' },
        { path: 'iterations', name: 'project-iterations', component: () => import('@/views/Iterations.vue') },
        { path: 'requirements', name: 'project-requirements', component: () => import('@/views/Requirements.vue') },
      ],
    },
    { path: '/iteration/:id', name: 'iteration-detail', component: () => import('@/views/IterationDetail.vue') },
    { path: '/requirement/:id', name: 'requirement-detail', component: () => import('@/views/RequirementDetail.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
    { path: '/iterations', name: 'iterations', component: () => import('@/views/Iterations.vue') },
    { path: '/requirements', name: 'requirements', component: () => import('@/views/Requirements.vue') },
    { path: '/standup', name: 'standup', component: () => import('@/views/Standup.vue') },
    { path: '/mcp-config', name: 'mcp-config', component: () => import('@/views/McpConfig.vue') },
    { path: '/documents', name: 'documents', component: () => import('@/views/Documents.vue') },
    { path: '/modules', name: 'modules', component: () => import('@/views/Modules.vue') },
    { path: '/webhooks', name: 'webhooks', component: () => import('@/views/Webhooks.vue') },
    { path: '/users', name: 'users', component: () => import('@/views/Users.vue') },
    { path: '/settings', name: 'settings', component: () => import('@/views/Settings.vue') },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  const auth = useAuthStore()
  if (!auth.isLoggedIn) {
    return { name: 'login' }
  }
})

export default router
