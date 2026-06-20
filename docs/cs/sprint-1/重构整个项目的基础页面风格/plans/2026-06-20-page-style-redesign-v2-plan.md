# 页面风格重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 14+ 页面重构为 TAPD 企业蓝色风格，引入 Element Plus 组件库统一 UI

**Architecture:** 引入 Element Plus 作为 UI 组件库，通过 CSS 变量覆盖实现主题定制，侧边栏改造为 ElMenu 组件，表格/表单/弹窗分别统一为 ElTable/ElForm/ElDialog

**Tech Stack:** Vue 3, Element Plus, TypeScript, Vite

---

## Global Constraints

- Element Plus 版本: ^2.5.x（最新稳定版）
- 图标库: @element-plus/icons-vue
- CSS 变量覆盖在 main.css 中完成
- 所有页面须使用 ElTable/ElForm/ElDialog 组件
- TDD 强制：每个任务必须包含 RED→GREEN→REFACTOR 步骤

---

## 文件结构

```
frontend/src/
├── assets/main.css                    # 全局样式 + Element Plus 变量覆盖
├── components/
│   └── Layout.vue                    # 公共布局组件（侧边栏+主内容区）
├── views/                            # 各页面视图（按优先级分批重构）
│   ├── Projects.vue                  # P0
│   ├── Iterations.vue                # P0
│   ├── Requirements.vue              # P0
│   ├── ProjectDetail.vue             # P0
│   ├── IterationDetail.vue           # P1
│   ├── RequirementDetail.vue        # P1
│   ├── Dashboard.vue                # P2
│   ├── Standup.vue                  # P2
│   ├── Settings.vue                  # P3
│   ├── Users.vue                    # P3
│   ├── McpConfig.vue                # P3
│   ├── Modules.vue                  # P3
│   ├── Webhooks.vue                 # P3
│   ├── Documents.vue                # P3
│   └── Login.vue                    # P3
└── router/index.ts                  # 路由（可能需要调整）
```

---

## Task 1: 安装 Element Plus 依赖

**Files:**
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: 无
- Produces: Element Plus, @element-plus/icons-vue 依赖

- [ ] **Step 1: 安装 Element Plus 及图标库**

```bash
cd frontend
npm install element-plus @element-plus/icons-vue
```

- [ ] **Step 2: 验证安装**

```bash
npm list element-plus @element-plus/icons-vue
```

Expected: 显示版本号

- [ ] **Step 3: 提交**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "deps: install element-plus and icons"
```

---

## Task 2: 配置 Element Plus 主题变量

**Files:**
- Modify: `frontend/src/assets/main.css:1-30`

**Interfaces:**
- Consumes: 无
- Produces: Element Plus 主题变量覆盖

- [ ] **Step 1: 添加 Element Plus 主题变量覆盖**

在 `main.css` 顶部 `:root` 中添加：

```css
:root {
  /* 已有变量（保留） */
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

  /* Element Plus 主题覆盖 */
  --el-color-primary: #2d5bff;
  --el-color-primary-light-3: #5a7bff;
  --el-color-primary-light-5: #8aa3ff;
  --el-color-primary-light-7: #b8cbff;
  --el-color-primary-light-8: #d0deff;
  --el-color-primary-light-9: #e8eeff;
  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', 'Helvetica Neue', Arial, sans-serif;
  --el-text-color-primary: #1f2329;
  --el-text-color-regular: #646a73;
  --el-text-color-secondary: #969ba4;
  --el-fill-color-blank: #ffffff;
  --el-bg-color: #f5f7ff;
  --el-border-color: #e8e9eb;
  --el-border-color-light: #f0f1f5;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/assets/main.css
git commit -m "style: add Element Plus theme variable overrides"
```

---

## Task 3: 创建公共布局组件

**Files:**
- Create: `frontend/src/components/Layout.vue`

**Interfaces:**
- Consumes: router/index.ts 路由配置
- Produces: Layout 组件，供所有页面复用

- [ ] **Step 1: 创建 Layout.vue**

```vue
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
          <el-dropdown>
            <div class="topbar-user">
              <div class="user-avatar">{{ userInitial }}</div>
              <span>{{ username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
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
  Grid, Files, Connection, User, Setting
} from '@element-plus/icons-vue'

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
}
const pageTitle = computed(() => pageTitleMap[currentRoute.value] || '')

const username = computed(() => auth.user?.name || '用户')
const userInitial = computed(() => username.value.charAt(0).toUpperCase())

const logout = () => {
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
```

- [ ] **Step 2: 更新 router/index.ts 使用 Layout**

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/components/Layout.vue'),
      children: [
        { path: 'projects', name: 'projects', component: () => import('@/views/Projects.vue') },
        { path: 'iterations', name: 'iterations', component: () => import('@/views/Iterations.vue') },
        { path: 'requirements', name: 'requirements', component: () => import('@/views/Requirements.vue') },
        { path: 'project/:id', name: 'project-detail', component: () => import('@/views/ProjectDetail.vue') },
        { path: 'iteration/:id', name: 'iteration-detail', component: () => import('@/views/IterationDetail.vue') },
        { path: 'requirement/:id', name: 'requirement-detail', component: () => import('@/views/RequirementDetail.vue') },
        { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
        { path: 'standup', name: 'standup', component: () => import('@/views/Standup.vue') },
        { path: 'modules', name: 'modules', component: () => import('@/views/Modules.vue') },
        { path: 'documents', name: 'documents', component: () => import('@/views/Documents.vue') },
        { path: 'webhooks', name: 'webhooks', component: () => import('@/views/Webhooks.vue') },
        { path: 'users', name: 'users', component: () => import('@/views/Users.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/Settings.vue') },
        { path: 'mcp-config', name: 'mcp-config', component: () => import('@/views/McpConfig.vue') },
      ],
    },
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
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/Layout.vue frontend/src/router/index.ts
git commit -m "feat: add Layout component with ElMenu sidebar"
```

---

## Task 4: 重构 Projects 页面

**Files:**
- Modify: `frontend/src/views/Projects.vue`

**Interfaces:**
- Consumes: projectsApi
- Produces: 使用 ElTable/ElInput/ElButton/ElDialog 的 Projects 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

```vue
<template>
  <div class="projects-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">项目管理</h1>
        <span class="text-muted text-medium" style="margin-left:12px;">{{ projects.length }} 个项目</span>
      </div>
      <div class="header-right">
        <el-input v-model="search" placeholder="搜索项目..." style="width:200px;" clearable />
        <el-button type="primary" @click="showCreateModal = true">
          <el-icon><Plus /></el-icon> 创建项目
        </el-button>
      </div>
    </div>

    <el-table :data="filteredProjects" stripe style="width:100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="name" label="项目名称" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" :underline="false" @click="$router.push(`/project/${row.id}`)">
            {{ row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          <span class="text-muted">{{ row.description || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">
          <span class="text-muted text-small">{{ formatDate(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="$router.push(`/project/${row.id}`)">查看</el-button>
          <el-button size="small" text type="danger" @click="deleteProject(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateModal" title="创建项目" width="500px">
      <el-form :model="newProject" label-position="top">
        <el-form-item label="项目名称" required>
          <el-input v-model="newProject.name" placeholder="如：CodeSeer Web" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="newProject.description" type="textarea" placeholder="简要描述项目目标..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateModal = false">取消</el-button>
        <el-button type="primary" :disabled="!newProject.name.trim()" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { projectsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const projects = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const selected = ref<string[]>([])
const search = ref('')
const newProject = ref({ name: '', description: '' })

const filteredProjects = computed(() => {
  if (!search.value.trim()) return projects.value
  const q = search.value.trim().toLowerCase()
  return projects.value.filter((p: any) => p.name.toLowerCase().includes(q))
})

const handleSelectionChange = (rows: any[]) => {
  selected.value = rows.map(r => r.id)
}

const statusType = (s: string) => ({ active: '', archived: 'info', completed: 'success' }[s] || 'info')
const statusText = (s: string) => ({ active: '进行中', archived: '已归档', completed: '已完成' }[s] || s)
const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

const fetchData = async () => {
  loading.value = true
  try { projects.value = (await projectsApi.list()).data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

const createProject = async () => {
  try {
    await projectsApi.create(newProject.value)
    showCreateModal.value = false
    newProject.value = { name: '', description: '' }
    ElMessage.success('创建成功')
    fetchData()
  } catch (e) { console.error(e) }
}

const deleteProject = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除此项目？', '提示', { type: 'warning' })
    await projectsApi.delete(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

onMounted(fetchData)
</script>

<style scoped>
.projects-page { max-width: 1200px; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-left, .header-right { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Projects.vue
git commit -m "refactor: use Element Plus components in Projects page"
```

---

## Task 5: 重构 Iterations 页面

**Files:**
- Modify: `frontend/src/views/Iterations.vue`

**Interfaces:**
- Consumes: iterationsApi
- Produces: 使用 ElTable/ElSelect 的 Iterations 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

参考 Task 4 的模式，将 Iterations.vue 重构为使用：
- `el-table` 替代原生 table
- `el-select` 替代筛选器
- `el-button` 统一按钮
- `el-dialog` 替代创建弹窗
- `el-tag` 替代状态徽章

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Iterations.vue
git commit -m "refactor: use Element Plus components in Iterations page"
```

---

## Task 6: 重构 Requirements 页面

**Files:**
- Modify: `frontend/src/views/Requirements.vue`

**Interfaces:**
- Consumes: requirementsApi
- Produces: 使用 ElTable/ElSelect 的 Requirements 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

参考 Task 4 的模式，将 Requirements.vue 重构为使用：
- `el-table` 替代原生 table
- `el-select` 替代筛选器
- `el-button` 统一按钮
- `el-dialog` 替代创建弹窗
- `el-tag` 替代优先级徽章

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Requirements.vue
git commit -m "refactor: use Element Plus components in Requirements page"
```

---

## Task 7: 重构 ProjectDetail 页面

**Files:**
- Modify: `frontend/src/views/ProjectDetail.vue`

**Interfaces:**
- Consumes: projectsApi, iterationsApi, requirementsApi
- Produces: 使用 ElTabs/ElTable 的 ProjectDetail 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

将 ProjectDetail.vue 重构为使用：
- `el-tabs` 替代自定义 Tab
- `el-table` 替代原生表格
- `el-button` 统一按钮

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/ProjectDetail.vue
git commit -m "refactor: use Element Plus components in ProjectDetail page"
```

---

## Task 8: 重构 IterationDetail 页面

**Files:**
- Modify: `frontend/src/views/IterationDetail.vue`

**Interfaces:**
- Consumes: iterationsApi, requirementsApi
- Produces: 使用 ElForm/ElInput 的 IterationDetail 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

将 IterationDetail.vue 重构为使用：
- `el-form` 替代原生表单
- `el-input` 替代输入框
- `el-button` 统一按钮

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/IterationDetail.vue
git commit -m "refactor: use Element Plus components in IterationDetail page"
```

---

## Task 9: 重构 RequirementDetail 页面

**Files:**
- Modify: `frontend/src/views/RequirementDetail.vue`

**Interfaces:**
- Consumes: requirementsApi
- Produces: 使用 ElForm/ElInput 的 RequirementDetail 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

将 RequirementDetail.vue 重构为使用：
- `el-form` 替代原生表单
- `el-input` 替代输入框
- `el-select` 替代下拉框
- `el-button` 统一按钮

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/RequirementDetail.vue
git commit -m "refactor: use Element Plus components in RequirementDetail page"
```

---

## Task 10: 重构 Dashboard 页面

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

**Interfaces:**
- Consumes: 各 API
- Produces: 使用 ElCard/ElStatistic 的 Dashboard 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

将 Dashboard.vue 重构为使用：
- `el-card` 替代统计卡片
- `el-statistic` 替代数字显示
- `el-row/el-col` 布局

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "refactor: use Element Plus components in Dashboard page"
```

---

## Task 11: 重构 Standup 页面

**Files:**
- Modify: `frontend/src/views/Standup.vue`

**Interfaces:**
- Consumes: standupApi
- Produces: 使用 ElDatePicker/ElCard 的 Standup 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

将 Standup.vue 重构为使用：
- `el-date-picker` 替代日期选择
- `el-card` 替代卡片
- `el-input` 替代文本框

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Standup.vue
git commit -m "refactor: use Element Plus components in Standup page"
```

---

## Task 12: 重构 P3 页面（Settings/Users/McpConfig/Modules/Webhooks/Documents）

**Files:**
- Modify: `frontend/src/views/Settings.vue`
- Modify: `frontend/src/views/Users.vue`
- Modify: `frontend/src/views/McpConfig.vue`
- Modify: `frontend/src/views/Modules.vue`
- Modify: `frontend/src/views/Webhooks.vue`
- Modify: `frontend/src/views/Documents.vue`

**Interfaces:**
- Consumes: 各模块 API
- Produces: 统一使用 Element Plus 组件的各页面

- [ ] **Step 1: 重构 Settings.vue**

- `el-form` + `el-form-item` 替代表单
- `el-switch` 替代开关
- `el-input` 替代输入框

- [ ] **Step 2: 重构 Users.vue**

- `el-table` 替代表格
- `el-dialog` 替代弹窗

- [ ] **Step 3: 重构 McpConfig.vue**

- `el-form` 替代表单
- `el-input` 替代输入框

- [ ] **Step 4: 重构 Modules.vue**

- `el-table` 替代表格
- `el-dialog` 替代弹窗

- [ ] **Step 5: 重构 Webhooks.vue**

- `el-table` 替代表格
- `el-dialog` 替代弹窗

- [ ] **Step 6: 重构 Documents.vue**

- `el-table` 替代表格
- `el-upload` 替代上传组件

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/Settings.vue frontend/src/views/Users.vue frontend/src/views/McpConfig.vue frontend/src/views/Modules.vue frontend/src/views/Webhooks.vue frontend/src/views/Documents.vue
git commit -m "refactor: use Element Plus components in P3 pages"
```

---

## Task 13: 重构 Login 页面

**Files:**
- Modify: `frontend/src/views/Login.vue`

**Interfaces:**
- Consumes: authStore
- Produces: 使用 ElForm/ElInput 的 Login 页面

- [ ] **Step 1: 重构为 Element Plus 组件**

将 Login.vue 重构为使用：
- `el-form` + `el-form-item` 替代表单
- `el-input` 替代输入框
- `el-button` 替代按钮

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Login.vue
git commit -m "refactor: use Element Plus components in Login page"
```

---

## Task 14: 全局样式检查与微调

**Files:**
- Modify: `frontend/src/assets/main.css`

**Interfaces:**
- Consumes: 所有页面
- Produces: 统一协调的全局样式

- [ ] **Step 1: 检查并补充 CSS 变量覆盖**

确保以下 Element Plus 组件样式符合 TAPD 风格：
- `el-table` 圆角、边框、hover
- `el-dialog` 圆角
- `el-button` 圆角、阴影
- `el-input` 圆角
- `el-select` 圆角
- `el-tag` 样式

- [ ] **Step 2: 提交**

```bash
git add frontend/src/assets/main.css
git commit -m "style: fine-tune Element Plus theme overrides"
```

---

## 验收标准检查清单

- [ ] Element Plus 主题变量覆盖完成
- [ ] 侧边栏改为 ElMenu 图标模式
- [ ] 所有表格页面统一使用 ElTable
- [ ] 所有表单页面统一使用 ElForm
- [ ] 所有弹窗统一使用 ElDialog
- [ ] 14+ 页面全部重构完成
- [ ] 整体视觉符合 TAPD 风格
