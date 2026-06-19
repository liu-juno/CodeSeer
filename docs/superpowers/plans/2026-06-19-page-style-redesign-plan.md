# 页面风格重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将项目前端从 AI 化紫/靛蓝风格重构为 TAPD 企业蓝色系风格

**Architecture:** 通过修改全局 CSS 变量系统实现配色统一，改造侧边栏为图标模式，新增顶部 Tab 导航，调整路由为嵌套结构，逐个重构优先页面组件。

**Tech Stack:** Vue 3, Vue Router 4, TypeScript, Vite

## Global Constraints

- 主色：`#2d5bff`
- 背景色：`#f5f7ff`
- 卡片圆角：12px
- 卡片阴影：`0 2px 8px rgba(0,0,0,0.08)`
- 侧边栏宽度：56px
- 路由结构：嵌套形式 `/project/:id/iterations`, `/project/:id/requirements`

---

## 文件结构

```
frontend/src/
├── assets/main.css          # 全局样式（配色、圆角、阴影）
├── App.vue                  # 根组件（侧边栏 + 顶部 Tab 布局）
├── router/index.ts          # 路由配置（改为嵌套）
├── components/
│   ├── Sidebar.vue          # 侧边栏（图标模式）
│   └── TopTab.vue           # 顶部 Tab 导航
└── views/
    ├── Projects.vue         # 项目列表
    ├── Iterations.vue       # 迭代列表
    ├── Requirements.vue     # 需求列表
    ├── ProjectDetail.vue    # 项目详情
    ├── IterationDetail.vue  # 迭代详情
    └── RequirementDetail.vue # 需求详情
```

---

## 任务列表

### Task 1: 全局样式重构

**Files:**
- Modify: `frontend/src/assets/main.css:1-916`

**Interfaces:**
- Produces: CSS 变量系统供全局使用

- [ ] **Step 1: 备份现有 main.css**

```bash
cp frontend/src/assets/main.css frontend/src/assets/main.css.bak
```

- [ ] **Step 2: 重写 CSS 变量和基础样式**

```css
:root {
  --color-primary: #2d5bff;
  --color-primary-hover: #1e4ae8;
  --color-bg: #f5f7ff;
  --color-sidebar-bg: #ffffff;
  --color-sidebar-border: #e8e9eb;
  --color-text-primary: #1f2329;
  --color-text-secondary: #646a73;
  --color-success: #00a870;
  --color-warning: #ff9a2e;
  --color-error: #ff4533;
  
  --radius-card: 12px;
  --radius-btn: 8px;
  --radius-input: 8px;
  --radius-modal: 14px;
  
  --shadow-card: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-modal: 0 20px 60px rgba(0,0,0,0.15);
  
  --sidebar-width: 56px;
  --topbar-height: 48px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text-primary);
  background-color: var(--color-bg);
}
```

- [ ] **Step 3: 更新侧边栏样式**

```css
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--color-sidebar-bg);
  color: var(--color-text-primary);
  padding: 0;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-sidebar-border);
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 8px;
  border-bottom: 1px solid var(--color-sidebar-border);
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: var(--color-primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background-color: var(--color-bg);
  color: var(--color-primary);
}

.nav-item.router-link-active {
  background-color: var(--color-bg);
  color: var(--color-primary);
}
```

- [ ] **Step 4: 更新顶部栏样式**

```css
.topbar {
  height: var(--topbar-height);
  background-color: var(--color-sidebar-bg);
  border-bottom: 1px solid var(--color-sidebar-border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}
```

- [ ] **Step 5: 更新卡片样式**

```css
.card {
  background-color: #ffffff;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-sidebar-border);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-card);
}
```

- [ ] **Step 6: 更新按钮样式**

```css
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 1px 3px rgba(45, 91, 255, 0.3);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 2px 6px rgba(45, 91, 255, 0.4);
}

.btn-secondary {
  background-color: #ffffff;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
```

- [ ] **Step 7: 更新表格样式**

```css
.table th {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text-secondary);
  background-color: var(--color-bg);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table tbody tr:hover {
  background-color: #fafafa;
}
```

- [ ] **Step 8: 更新状态徽章**

```css
.status-badge.in_progress {
  background: #e6f0ff;
  color: var(--color-primary);
}

.status-badge.completed {
  background: #dff5eb;
  color: var(--color-success);
}

.status-badge.draft {
  background: #f5f5f5;
  color: #969ba4;
}
```

- [ ] **Step 9: 验证样式变更**

启动前端开发服务器，检查样式是否正确应用。

- [ ] **Step 10: 提交**

```bash
git add frontend/src/assets/main.css
git commit -m "feat: apply TAPD color scheme and global styles"
```

---

### Task 2: 侧边栏组件改为图标模式

**Files:**
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Consumes: CSS 变量 `--sidebar-width`, `--color-primary`
- Produces: 56px 宽图标侧边栏

- [ ] **Step 1: 读取 App.vue 了解当前侧边栏结构**

- [ ] **Step 2: 修改侧边栏 HTML 结构，只保留图标**

```vue
<aside class="sidebar">
  <div class="logo">
    <div class="logo-icon">CS</div>
  </div>
  <nav class="nav">
    <router-link to="/projects" class="nav-item" title="项目管理">
      <span class="nav-icon">📁</span>
    </router-link>
    <router-link to="/iterations" class="nav-item" title="迭代管理">
      <span class="nav-icon">🔄</span>
    </router-link>
    <router-link to="/requirements" class="nav-item" title="需求管理">
      <span class="nav-icon">📋</span>
    </router-link>
    <router-link to="/dashboard" class="nav-item" title="仪表盘">
      <span class="nav-icon">📊</span>
    </router-link>
    <router-link to="/settings" class="nav-item" title="设置">
      <span class="nav-icon">⚙️</span>
    </router-link>
  </nav>
</aside>
```

- [ ] **Step 3: 添加 nav-icon 样式**

```css
.nav-icon {
  font-size: 18px;
}
```

- [ ] **Step 4: 验证侧边栏显示**

确认侧边栏宽度为 56px，图标居中显示。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: convert sidebar to icon-only mode"
```

---

### Task 3: 新增顶部 Tab 导航组件

**Files:**
- Create: `frontend/src/components/TopTab.vue`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Consumes: Vue Router current route
- Produces: TopTab 组件，触发面包屑更新

- [ ] **Step 1: 创建 TopTab.vue**

```vue
<template>
  <div class="toptab">
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
  if (route.path.includes('/requirement/')) return '需求'
  return ''
})

const currentName = computed(() => {
  if (route.path.endsWith('/iterations')) return '迭代管理'
  if (route.path.endsWith('/requirements')) return '需求管理'
  if (route.path.includes('/iteration/')) return '迭代详情'
  if (route.path.includes('/requirement/')) return '需求详情'
  return ''
})

const isActiveTab = (path: string) => route.path === path

const switchTab = (path: string) => {
  router.push(path)
}

const goToParent = () => {
  if (route.path.includes('/project/')) {
    router.push('/projects')
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
```

- [ ] **Step 2: 在 App.vue 中集成 TopTab**

在 main-content 区域顶部添加 TopTab 组件：

```vue
<div class="main-content">
  <TopTab />
  <div class="content">
    <router-view />
  </div>
</div>
```

- [ ] **Step 3: 验证顶部 Tab 显示**

检查路由变化时 Tab 是否正确高亮。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/TopTab.vue frontend/src/App.vue
git commit -m "feat: add top tab navigation component"
```

---

### Task 4: 路由结构调整为嵌套结构

**Files:**
- Modify: `frontend/src/router/index.ts`

**Interfaces:**
- Consumes: Vue Router
- Produces: 嵌套路由 `/project/:id/iterations`, `/project/:id/requirements`

- [ ] **Step 1: 读取当前 router/index.ts**

- [ ] **Step 2: 修改路由配置**

```typescript
const routes = [
  {
    path: '/',
    redirect: '/projects'
  },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('../views/Projects.vue')
  },
  {
    path: '/project/:id',
    component: () => import('../views/ProjectDetail.vue'),
    children: [
      {
        path: '',
        redirect: 'iterations'
      },
      {
        path: 'iterations',
        name: 'project-iterations',
        component: () => import('../views/Iterations.vue')
      },
      {
        path: 'requirements',
        name: 'project-requirements',
        component: () => import('../views/Requirements.vue')
      }
    ]
  },
  {
    path: '/iteration/:id',
    name: 'iteration-detail',
    component: () => import('../views/IterationDetail.vue')
  },
  {
    path: '/requirement/:id',
    name: 'requirement-detail',
    component: () => import('../views/RequirementDetail.vue')
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/Settings.vue')
  }
]
```

- [ ] **Step 3: 更新视图组件的路由跳转**

修改 Projects.vue、Iterations.vue、Requirements.vue 中的跳转链接。

- [ ] **Step 4: 验证路由跳转**

测试嵌套路由是否正常工作。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: restructure routes to nested format"
```

---

### Task 5: Projects 页面重构

**Files:**
- Modify: `frontend/src/views/Projects.vue`

**Interfaces:**
- Consumes: 全局 CSS 变量
- Produces: TAPD 风格的 Projects 页面

- [ ] **Step 1: 读取当前 Projects.vue**

- [ ] **Step 2: 应用 TAPD 风格样式**

确保页面使用 `.card` 样式、`.btn-primary`、`.table` 等组件。

- [ ] **Step 3: 验证显示效果**

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/Projects.vue
git commit -m "feat: restyle Projects page to TAPD style"
```

---

### Task 6: Iterations 页面重构

**Files:**
- Modify: `frontend/src/views/Iterations.vue`

**Interfaces:**
- Consumes: 全局 CSS 变量
- Produces: TAPD 风格的 Iterations 页面

- [ ] **Step 1: 读取当前 Iterations.vue**

- [ ] **Step 2: 应用 TAPD 风格样式**

- [ ] **Step 3: 验证显示效果**

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/Iterations.vue
git commit -m "feat: restyle Iterations page to TAPD style"
```

---

### Task 7: Requirements 页面重构

**Files:**
- Modify: `frontend/src/views/Requirements.vue`

**Interfaces:**
- Consumes: 全局 CSS 变量
- Produces: TAPD 风格的 Requirements 页面

- [ ] **Step 1: 读取当前 Requirements.vue**

- [ ] **Step 2: 应用 TAPD 风格样式**

- [ ] **Step 3: 验证显示效果**

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/Requirements.vue
git commit -m "feat: restyle Requirements page to TAPD style"
```

---

## 自检清单

- [ ] 配色系统已应用 `#2d5bff` 主色
- [ ] 侧边栏宽度为 56px 图标模式
- [ ] 顶部 Tab 导航正常工作
- [ ] 路由结构为嵌套形式
- [ ] 卡片圆角 12px 带阴影
- [ ] Projects/Iterations/Requirements 页面样式统一

---

## 实施选项

**Plan complete and saved to `docs/superpowers/plans/2026-06-19-page-style-redesign-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**