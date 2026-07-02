<template>
  <aside class="module-sidebar">
    <div class="sidebar-project-name">
      <el-tooltip
        :content="projectName"
        placement="right"
        :disabled="projectName.length < 18"
      >
        <span class="project-name-text">{{ projectName }}</span>
      </el-tooltip>
    </div>

    <nav class="sidebar-nav">
      <!-- 工作模块 -->
      <router-link to="/dashboard" class="nav-item">
        <el-icon><DataLine /></el-icon>
        <span>概览</span>
      </router-link>
      <router-link to="/requirements" class="nav-item">
        <el-icon><Document /></el-icon>
        <span>需求</span>
      </router-link>
      <router-link to="/defects" class="nav-item">
        <el-icon><WarnTriangleFilled /></el-icon>
        <span>缺陷</span>
      </router-link>
      <router-link to="/iterations" class="nav-item">
        <el-icon><Timer /></el-icon>
        <span>迭代</span>
      </router-link>

      <div class="nav-divider" />

      <!-- 资源 -->
      <router-link to="/documents" class="nav-item">
        <el-icon><Files /></el-icon>
        <span>文档</span>
      </router-link>
      <router-link to="/api-endpoints" class="nav-item">
        <el-icon><Connection /></el-icon>
        <span>API</span>
      </router-link>
      <router-link to="/modules" class="nav-item">
        <el-icon><Grid /></el-icon>
        <span>模块</span>
      </router-link>
      <router-link to="/standup" class="nav-item">
        <el-icon><Calendar /></el-icon>
        <span>站会</span>
      </router-link>

      <div class="nav-divider" />

      <!-- 管理 -->
      <router-link v-if="isProjectAdmin" :to="membersLink" class="nav-item" active-class="" exact-active-class="" :class="{ 'router-link-active': isMembersActive }">
        <el-icon><User /></el-icon>
        <span>成员</span>
      </router-link>
      <router-link :to="settingsLink" class="nav-item" active-class="" exact-active-class="" :class="{ 'router-link-active': isSettingsActive }">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import {
  DataLine, Document, WarnTriangleFilled, Timer,
  Files, Calendar, User, Setting, Grid, Connection
} from '@element-plus/icons-vue'

const route = useRoute()
const projectStore = useProjectStore()
const authStore = useAuthStore()
const projectName = computed(() => projectStore.currentProject?.name || '未选择项目')

const isProjectAdmin = computed(() =>
  authStore.user?.role === 'admin' || projectStore.currentUserProjectRole === 'admin'
)
const settingsLink = computed(() =>
  projectStore.currentProjectId
    ? { path: `/project/${projectStore.currentProjectId}/settings`, query: { tab: 'info' } }
    : '/settings'
)
const membersLink = computed(() =>
  projectStore.currentProjectId
    ? { path: `/project/${projectStore.currentProjectId}/settings`, query: { tab: 'members' } }
    : '/users'
)
const isOnSettingsPage = computed(() =>
  projectStore.currentProjectId && route.path === `/project/${projectStore.currentProjectId}/settings`
)
const isSettingsActive = computed(() => isOnSettingsPage.value && route.query.tab !== 'members')
const isMembersActive = computed(() => isOnSettingsPage.value && route.query.tab === 'members')
</script>

<style scoped>
.module-sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-project-name {
  height: var(--topbar-height);
  padding: 0 1rem;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-default);
  flex-shrink: 0;
  overflow: hidden;
}

.project-name-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0.375rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.router-link-active {
  background: var(--bg-hover);
  color: var(--color-primary);
  border-left-color: var(--color-primary);
  font-weight: 500;
}

.nav-divider {
  height: 1px;
  background: var(--border-light);
  margin: 0.375rem 1rem;
}
</style>
