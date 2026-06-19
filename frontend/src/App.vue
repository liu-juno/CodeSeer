<template>
  <router-view v-if="route.name === 'login'" />
  <div v-else class="app-container">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">⚡</div>
        <span class="logo-text">CodeSeer</span>
      </div>

      <nav class="nav">
        <span class="nav-section-label">主菜单</span>
        <router-link to="/" class="nav-item" exact-active-class="router-link-active">
          <span class="nav-icon">◈</span>
          <span>工作台</span>
        </router-link>
        <router-link to="/requirements" class="nav-item">
          <span class="nav-icon">◇</span>
          <span>需求</span>
        </router-link>
        <router-link to="/iterations" class="nav-item">
          <span class="nav-icon">↻</span>
          <span>迭代</span>
        </router-link>
        <router-link to="/projects" class="nav-item">
          <span class="nav-icon">▦</span>
          <span>项目</span>
        </router-link>

        <div class="nav-divider"></div>
        <span class="nav-section-label">AI 流程</span>
        <router-link to="/standup" class="nav-item">
          <span class="nav-icon">◎</span>
          <span>早会视图</span>
        </router-link>
        <router-link to="/mcp-config" class="nav-item">
          <span class="nav-icon">⬡</span>
          <span>MCP 配置</span>
        </router-link>

        <div class="nav-divider"></div>
        <span class="nav-section-label">知识库</span>
        <router-link to="/documents" class="nav-item">
          <span class="nav-icon">▤</span>
          <span>文档管理</span>
        </router-link>
        <router-link to="/modules" class="nav-item">
          <span class="nav-icon">⬡</span>
          <span>模块知识库</span>
        </router-link>

        <div class="nav-divider"></div>
        <span class="nav-section-label">系统</span>
        <router-link to="/webhooks" class="nav-item">
          <span class="nav-icon">⌬</span>
          <span>Webhook 配置</span>
        </router-link>
        <router-link to="/users" class="nav-item">
          <span class="nav-icon">☉</span>
          <span>用户与角色</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <span class="nav-icon">⚙</span>
          <span>系统设置</span>
        </router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <span class="topbar-title">{{ pageTitle }}</span>
          <span class="topbar-badge">AI Platform</span>
        </div>
        <div class="topbar-right">
          <div class="topbar-user" v-if="authStore.user">
            <div class="user-avatar">{{ userInitial }}</div>
            <span style="font-size:13px; color:#374151; font-weight:500;">{{ authStore.user.name }}</span>
            <button class="logout-btn" @click="handleLogout" title="退出登录">⏻</button>
          </div>
        </div>
      </header>
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const userInitial = computed(() => authStore.user?.name?.[0]?.toUpperCase() ?? '?')

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/': '工作台',
    '/requirements': '需求管理',
    '/iterations': '迭代管理',
    '/projects': '项目管理',
    '/standup': '早会视图',
    '/mcp-config': 'MCP 配置',
    '/documents': '文档管理',
    '/modules': '模块知识库',
    '/webhooks': 'Webhook 配置',
    '/users': '用户与角色',
    '/settings': '系统设置',
  }
  const path = route.path
  if (path.startsWith('/requirements/')) return '需求详情'
  if (path.startsWith('/iterations/')) return '迭代详情'
  if (path.startsWith('/projects/')) return '项目详情'
  return map[path] || 'CodeSeer'
})
</script>

<style scoped>
.logout-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  font-size: 16px;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1;
  transition: color 0.2s;
}
.logout-btn:hover { color: #ef4444; }
</style>
