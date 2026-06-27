<template>
  <div class="app-container">
    <aside class="sidebar" :class="{ expanded: !sidebarCollapsed }">
      <div class="logo">
        <div class="logo-icon">CS</div>
        <span v-if="!sidebarCollapsed" class="logo-text">CodeSeer</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="sidebarCollapsed"
        :collapse-transition="true"
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
        <el-menu-item index="/defects">
          <el-icon><WarnTriangleFilled /></el-icon>
          <template #title>缺陷管理</template>
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
      <div class="sidebar-footer" @click="toggleSidebar">
        <el-icon :size="18"><Expand v-if="sidebarCollapsed" /><Fold v-else /></el-icon>
        <span v-if="!sidebarCollapsed">收起</span>
      </div>
    </aside>
    <main class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <span class="topbar-title">{{ pageTitle }}</span>
          <template v-if="parentName && tabs.length > 0">
            <span class="topbar-sep">/</span>
            <span class="topbar-tabs">
              <span
                v-for="tab in tabs"
                :key="tab.path"
                :class="['topbar-tab', { active: isActiveTab(tab.path) }]"
                @click="switchTab(tab.path)"
              >
                {{ tab.name }}
              </span>
            </span>
          </template>
        </div>
        <div class="topbar-right">
          <el-dropdown trigger="click">
            <div class="topbar-user">
              <div class="user-avatar">{{ userInitial }}</div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
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
  Grid, Files, Connection, User, Setting,
  Fold, Expand, WarnTriangleFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const sidebarCollapsed = ref(false)
const currentRoute = computed(() => route.path)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const tabs = computed(() => {
  if (route.path.includes('/project/')) {
    return [
      { name: '概览', path: `/project/${route.params.id}` },
      { name: '迭代', path: `/project/${route.params.id}/iterations` },
      { name: '需求', path: `/project/${route.params.id}/requirements` }
    ]
  }
  return []
})

const pageTitle = computed(() => {
  const path = route.path

  // 详情页
  if (path.startsWith('/project/') && path !== `/project/${route.params.id}`) return ''
  if (path.includes('/iteration/')) return '迭代详情'
  if (path.includes('/requirement/')) return '需求详情'

  // 列表页
  const titleMap: Record<string, string> = {
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
    '/requirement/new': '创建需求',
  }
  return titleMap[path] || ''
})

const parentName = computed(() => {
  if (route.path.includes('/project/')) return '项目'
  if (route.path.includes('/iteration/')) return '迭代'
  if (route.path.includes('/requirement/')) return '需求'
  return ''
})

const isActiveTab = (path: string) => route.path === path

const switchTab = (path: string) => {
  router.push(path)
}

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
  width: 64px;
  background: #ffffff;
  border-right: 1px solid #e8e9eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.expanded {
  width: 200px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #e8e9eb;
  height: 64px;
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
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #1f2329;
  white-space: nowrap;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #e8e9eb;
  cursor: pointer;
  color: #909399;
  transition: all 0.2s;
}

.sidebar-footer:hover {
  background: #f5f7ff;
  color: #2d5bff;
}

.sidebar.expanded .sidebar-footer {
  justify-content: flex-start;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.topbar {
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e8e9eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2329;
}

.topbar-sep {
  color: #909399;
  margin: 0 4px;
}

.topbar-subtitle {
  font-size: 15px;
  color: #606266;
}

.topbar-tabs {
  display: flex;
  gap: 4px;
}

.topbar-tab {
  padding: 6px 12px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s;
}

.topbar-tab:hover {
  background: #f5f7ff;
  color: #2d5bff;
}

.topbar-tab.active {
  background: #e8e9eb;
  color: #2d5bff;
  font-weight: 500;
}

.topbar-right {
  display: flex;
  align-items: center;
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