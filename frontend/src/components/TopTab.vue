<template>
  <div class="toptab" v-if="parentName || currentName || tabs.length > 0">
    <div class="toptab-breadcrumb">
      <span v-if="parentName" class="toptab-parent" @click="goToParent">
        {{ parentName }}
      </span>
      <span v-if="parentName" class="toptab-separator">/</span>
      <span class="toptab-current">{{ currentName }}</span>
    </div>
    <div class="toptab-tabs" v-if="tabs.length > 0">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        :class="['toptab-tab', { active: isActiveTab(tab.path) }]"
        @click="switchTab(tab.path)"
      >
        {{ tab.name }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

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

const parentName = computed(() => {
  if (route.path.includes('/project/')) return '项目'
  if (route.path.includes('/iteration/')) return '迭代'
  if (route.path.includes('/requirement/') && route.path !== '/requirement/new') return '需求'
  return ''
})

const currentName = computed(() => {
  if (route.path.endsWith('/iterations')) return '迭代管理'
  if (route.path.endsWith('/requirements')) return '需求管理'
  if (route.path.includes('/iteration/')) return '迭代详情'
  if (route.path.includes('/requirement/') && route.path !== '/requirement/new') return '需求详情'
  return ''
})

const isActiveTab = (path: string) => route.path === path

const switchTab = (path: string) => {
  router.push(path)
}

const goToParent = () => {
  if (route.path.includes('/project/')) {
    router.push('/projects')
  } else if (route.path.includes('/iteration/')) {
    router.push('/projects')
  } else if (route.path.includes('/requirement/')) {
    router.push('/requirements')
  }
}
</script>

<style scoped>
.toptab {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 24px;
  background: #ffffff;
  border-bottom: 1px solid var(--color-sidebar-border);
}

.toptab-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.toptab-parent {
  color: var(--color-text-secondary);
  cursor: pointer;
}

.toptab-parent:hover {
  color: var(--color-primary);
}

.toptab-separator {
  color: var(--color-text-secondary);
}

.toptab-current {
  color: var(--color-text-primary);
  font-weight: 600;
}

.toptab-tabs {
  display: flex;
  gap: 4px;
}

.toptab-tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}

.toptab-tab:hover {
  color: var(--color-primary);
}

.toptab-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
</style>
