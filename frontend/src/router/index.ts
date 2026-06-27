import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    { path: '/projects/select', name: 'project-select', component: () => import('@/views/ProjectSelect.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/components/Layout.vue'),
      children: [
        { path: '', redirect: '/projects' },
        { path: 'projects', name: 'projects', component: () => import('@/views/Projects.vue') },
        { path: 'iterations', name: 'iterations', component: () => import('@/views/Iterations.vue') },
        { path: 'requirements', name: 'requirements', component: () => import('@/views/Requirements.vue') },
        { path: 'project/:id', name: 'project-detail', component: () => import('@/views/ProjectDetail.vue') },
        { path: 'project/:id/settings', name: 'project-settings', component: () => import('@/views/ProjectSettings.vue') },
        { path: 'iteration/:id', name: 'iteration-detail', component: () => import('@/views/IterationDetail.vue') },
        { path: 'requirement/:id', name: 'requirement-detail', component: () => import('@/views/RequirementDetail.vue') },
        { path: 'requirement/new', name: 'requirement-create', component: () => import('@/views/RequirementCreate.vue') },
        { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
        { path: 'standup', name: 'standup', component: () => import('@/views/Standup.vue') },
        { path: 'modules', name: 'modules', component: () => import('@/views/Modules.vue') },
        { path: 'documents', name: 'documents', component: () => import('@/views/Documents.vue') },
        { path: 'webhooks', name: 'webhooks', component: () => import('@/views/Webhooks.vue') },
        { path: 'users', name: 'users', component: () => import('@/views/Users.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/Settings.vue') },
        { path: 'mcp-config', name: 'mcp-config', component: () => import('@/views/McpConfig.vue') },
        {
          path: 'defects',
          children: [
            { path: '', component: () => import('@/views/Defects.vue') },
            { path: 'new', component: () => import('@/views/DefectCreate.vue') },
            { path: ':id', component: () => import('@/views/DefectDetail.vue') },
          ]
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()
  if (!auth.isLoggedIn) {
    return { name: 'login' }
  }

  const noProjectRoutes = ['project-select', 'login', 'register']
  if (noProjectRoutes.includes(to.name as string)) return true

  const projectStore = useProjectStore()
  projectStore.initFromStorage()

  if (!projectStore.currentProjectId) {
    return { name: 'project-select' }
  }

  return true
})

export default router
