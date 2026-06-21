<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">CS</div>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <template #title>项目管理</template>
        </el-menu-item>
        <el-menu-item index="/iterations">
          <el-icon><Timer /></el-icon>
          <template #title>迭代管理</template>
        </el-menu-item>
        <el-menu-item index="/requirements">
          <el-icon><Document /></el-icon>
          <template #title>需求管理</template>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/standup">
          <el-icon><Calendar /></el-icon>
          <template #title>站会</template>
        </el-menu-item>
        <el-menu-item index="/modules">
          <el-icon><Grid /></el-icon>
          <template #title>模块管理</template>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Files /></el-icon>
          <template #title>文档管理</template>
        </el-menu-item>
        <el-menu-item index="/webhooks">
          <el-icon><Connection /></el-icon>
          <template #title>Webhooks</template>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
      </el-menu>
    </aside>
    <main class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <span class="topbar-title">{{ pageTitle }}</span>
        </div>
        <div class="topbar-right">
          <el-dropdown trigger="click">
            <div class="topbar-user">
              <div class="user-avatar">{{ userInitial }}</div>
              <span>{{ username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      <TopTab />
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Folder, Timer, Document, DataLine, Calendar,
  Grid, Files, Connection, User, Setting
} from '@element-plus/icons-vue'
import TopTab from '@/components/TopTab.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const sidebarCollapsed = ref(true)
const currentRoute = computed(() => route.path)

const pageTitleMap: Record<string, string> = {
  '/projects': '项目管理',
  '/iterations': '迭代管理',
  '/requirements': '需求管理',
  '/dashboard': '仪表盘',
  '/standup': '站会',
  '/modules': '模块管理',
  '/documents': '文档管理',
  '/webhooks': 'Webhooks',
  '/users': '用户管理',
  '/settings': '设置',
  '/mcp-config': 'MCP 配置',
}
const pageTitle = computed(() => {
  const path = currentRoute.value
  if (path === '/requirement/new') return '需求 / 创建需求'
  if (path.startsWith('/project/')) return '项目详情'
  if (path.startsWith('/iteration/')) return '迭代详情'
  if (path.startsWith('/requirement/')) return '需求详情'
  return pageTitleMap[path] || ''
})

const username = computed(() => auth.user?.name || '用户')
const userInitial = computed(() => username.value.charAt(0).toUpperCase())

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 56px;
  background: #ffffff;
  border-right: 1px solid #e8e9eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 8px;
  border-bottom: 1px solid #e8e9eb;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: #2d5bff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: white;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.topbar {
  height: 48px;
  background: #ffffff;
  border-bottom: 1px solid #e8e9eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2329;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 7px;
}

.topbar-user:hover {
  background: #f5f7ff;
}

.user-avatar {
  width: 28px;
  height: 28px;
  background: #2d5bff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 28px;
  background: #f5f7ff;
}
</style>
