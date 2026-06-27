# UI/Layout Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor CodeSeer's layout from a single collapsible sidebar to a TAPD-inspired three-column layout (project Rail + module Sidebar + content area), with a persistent iteration context selector in the Topbar, a dual-mode CSS token system, and a manual dark mode toggle.

**Architecture:** Three-column flex layout — fixed-width project Rail, fixed-width module Sidebar, flex-1 main area containing AppTopbar + router-view. All sizing via `clamp()` CSS variables. `useTheme` composable manages `data-theme` on `<html>` and persists to localStorage. The project store gains `currentIterationId`; Topbar writes it; list views read it as an API query param.

**Tech Stack:** Vue 3 (Composition API), Pinia, Vue Router 4, Element Plus, Vite, Vitest + @vue/test-utils

## Global Constraints

- No hardcoded pixel values in layout or component `<style>` blocks — use `clamp()` and CSS custom property variables
- All colors reference CSS token variables (`var(--...)`); no raw hex values in component styles
- `any` in TypeScript only when the backend type is genuinely dynamic (existing pattern is `ref<any>`)
- Run `cd frontend && npm run test` to execute tests; `npm run dev` to start the dev server
- Commit after each task

---

## File Structure

**Create:**

| File | Responsibility |
|---|---|
| `frontend/src/composables/useTheme.ts` | Singleton: reads/writes localStorage, sets `data-theme` on `<html>`, exports reactive `isDark` + `toggle()` + `init()` |
| `frontend/src/components/ProjectRail.vue` | Leftmost fixed-width Rail: project icon list, active highlight, hover tooltip, create-project button |
| `frontend/src/components/ModuleSidebar.vue` | Module navigation sidebar: project name + three grouped nav sections with router-link active state |
| `frontend/src/components/AppTopbar.vue` | Topbar: iteration selector dropdown, breadcrumb, dark mode toggle, user avatar + logout |

**Modify:**

| File | Change |
|---|---|
| `frontend/src/assets/main.css` | Replace all tokens with dual-mode CSS variable system; add responsive `clamp()` layout sizing variables |
| `frontend/src/stores/project.ts` | Add `currentIterationId`, `currentIteration`, `setCurrentIteration()`, `clearCurrentIteration()` |
| `frontend/src/App.vue` | Call `useTheme().init()` on mount to restore persisted theme before render |
| `frontend/src/components/Layout.vue` | Rewrite to three-column shell: `<ProjectRail>` + `<ModuleSidebar>` + main area with `<AppTopbar>` + `<router-view>` |
| `frontend/src/views/IterationDetail.vue` | Add fixed info header (name, dates, status, progress bar) and internal sub-tabs (概览 / 需求 / 缺陷 / 成员) |

---

## Task 1: CSS Token System

**Files:**
- Modify: `frontend/src/assets/main.css`

**Interfaces:**
- Produces: CSS custom properties consumed by all subsequent component tasks — `--rail-width`, `--sidebar-width`, `--topbar-height`, `--bg-base`, `--bg-surface`, `--bg-elevated`, `--bg-hover`, `--border-default`, `--border-light`, `--text-primary`, `--text-secondary`, `--text-muted`, `--color-primary`, `--rail-bg`, `--sidebar-bg`, and all `--el-*` Element Plus overrides. Dark variants under `[data-theme="dark"]`.

- [ ] **Step 1: Replace main.css with the dual-mode token system**

Overwrite the entire file:

```css
/* ── Layout sizing ─────────────────────────────────────────── */
:root {
  --rail-width:     clamp(40px, 3.5vw, 56px);
  --sidebar-width:  clamp(180px, 14vw, 220px);
  --topbar-height:  clamp(48px, 4.5vh, 60px);

  /* Light theme */
  --bg-base:        #f4f5f7;
  --bg-surface:     #ffffff;
  --bg-elevated:    #ffffff;
  --bg-hover:       #f0f1f3;
  --border-default: #e4e5e8;
  --border-light:   #f0f1f5;
  --text-primary:   #1f2329;
  --text-secondary: #646a73;
  --text-muted:     #969ba4;
  --color-primary:  #2d5bff;
  --color-primary-hover: #1e4ae8;
  --color-success:  #00a870;
  --color-warning:  #ff9a2e;
  --color-error:    #ff4533;
  --rail-bg:        #f0f1f3;
  --sidebar-bg:     #ffffff;

  /* Radius / Shadow */
  --radius-card:  12px;
  --radius-btn:   8px;
  --radius-input: 8px;
  --radius-modal: 14px;
  --shadow-card:  0 2px 8px rgba(0,0,0,0.08);
  --shadow-modal: 0 20px 60px rgba(0,0,0,0.15);

  /* Element Plus overrides */
  --el-color-primary:          #2d5bff;
  --el-color-primary-light-3:  #5a7bff;
  --el-color-primary-light-5:  #8aa3ff;
  --el-color-primary-light-7:  #b8cbff;
  --el-color-primary-light-8:  #d0deff;
  --el-color-primary-light-9:  #e8eeff;
  --el-border-radius-base:     8px;
  --el-border-radius-small:    6px;
  --el-font-family:            -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', 'Helvetica Neue', Arial, sans-serif;
  --el-text-color-primary:     var(--text-primary);
  --el-text-color-regular:     var(--text-secondary);
  --el-text-color-secondary:   var(--text-muted);
  --el-fill-color-blank:       var(--bg-surface);
  --el-bg-color:               var(--bg-base);
  --el-border-color:           var(--border-default);
  --el-border-color-light:     var(--border-light);
  --el-table-border-color:     var(--border-default);
  --el-table-header-bg-color:  var(--bg-base);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-dialog-border-radius:   14px;
  --el-button-border-radius:   8px;
  --el-input-border-radius:    8px;
}

/* ── Dark theme overrides ───────────────────────────────────── */
[data-theme="dark"] {
  --bg-base:        #1a1b1e;
  --bg-surface:     #25262b;
  --bg-elevated:    #2c2d33;
  --bg-hover:       #373a40;
  --border-default: #373a40;
  --border-light:   #2c2d33;
  --text-primary:   #c1c2c5;
  --text-secondary: #909296;
  --text-muted:     #5c5f66;
  --color-primary:  #4c7bff;
  --color-primary-hover: #6b93ff;
  --rail-bg:        #141517;
  --sidebar-bg:     #1e1f23;

  --el-color-primary:          #4c7bff;
  --el-color-primary-light-3:  #6b93ff;
  --el-color-primary-light-5:  #8aabff;
  --el-color-primary-light-7:  #a9c2ff;
  --el-color-primary-light-8:  #c0d3ff;
  --el-color-primary-light-9:  #d8e4ff;
  --el-text-color-primary:     var(--text-primary);
  --el-text-color-regular:     var(--text-secondary);
  --el-text-color-secondary:   var(--text-muted);
  --el-fill-color-blank:       var(--bg-surface);
  --el-bg-color:               var(--bg-base);
  --el-border-color:           var(--border-default);
  --el-border-color-light:     var(--border-light);
  --el-table-border-color:     var(--border-default);
  --el-table-header-bg-color:  var(--bg-elevated);
  --el-table-row-hover-bg-color: var(--bg-hover);
}

/* ── Base reset ─────────────────────────────────────────────── */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  background-color: var(--bg-base);
}

/* ── Utility classes ────────────────────────────────────────── */
.text-muted     { color: var(--text-muted); }
.text-secondary { color: var(--text-secondary); }
.text-small     { font-size: 0.8125rem; }
.text-primary   { color: var(--color-primary); }
.card-title     { font-weight: 600; font-size: 0.9375rem; color: var(--text-primary); }

/* ── Responsive layout breakpoints ─────────────────────────── */
@media (max-width: 1280px) {
  :root { --sidebar-width: clamp(48px, 5vw, 64px); }
}
@media (max-width: 960px) {
  :root { --rail-width: 0px; }
}
```

- [ ] **Step 2: Start dev server and verify no obvious breakage**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 and confirm the existing pages still render (colors may shift — that is expected and correct).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/assets/main.css
git commit -m "refactor(ui): replace CSS tokens with dual-mode variable system"
```

---

## Task 2: useTheme Composable + App.vue Init

**Files:**
- Create: `frontend/src/composables/useTheme.ts`
- Create: `frontend/src/tests/useTheme.test.ts`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Produces: `useTheme()` returning `{ isDark: Ref<boolean>, toggle: () => void, init: () => void }`
- Consumes: nothing (reads localStorage, mutates `document.documentElement`)

- [ ] **Step 1: Write the failing test**

Create `frontend/src/tests/useTheme.test.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'

const setAttributeMock = vi.fn()
vi.stubGlobal('document', {
  documentElement: { setAttribute: setAttributeMock }
})

describe('useTheme', () => {
  beforeEach(async () => {
    localStorage.clear()
    setAttributeMock.mockClear()
    vi.resetModules()
  })

  it('init() applies light theme when nothing is stored', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const { init } = useTheme()
    init()
    expect(setAttributeMock).toHaveBeenCalledWith('data-theme', 'light')
  })

  it('init() applies dark theme when localStorage has "dark"', async () => {
    localStorage.setItem('codeseer-theme', 'dark')
    const { useTheme } = await import('@/composables/useTheme')
    const { isDark, init } = useTheme()
    init()
    expect(isDark.value).toBe(true)
    expect(setAttributeMock).toHaveBeenCalledWith('data-theme', 'dark')
  })

  it('toggle() flips isDark from false to true', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const { isDark, init, toggle } = useTheme()
    init()
    expect(isDark.value).toBe(false)
    toggle()
    expect(isDark.value).toBe(true)
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend && npm run test -- useTheme
```

Expected: FAIL with "Cannot find module '@/composables/useTheme'"

- [ ] **Step 3: Implement useTheme**

Create `frontend/src/composables/useTheme.ts`:

```typescript
import { ref, watch } from 'vue'

const STORAGE_KEY = 'codeseer-theme'
const isDark = ref(false)
let _initialized = false

export function useTheme() {
  function init() {
    if (_initialized) return
    _initialized = true
    isDark.value = localStorage.getItem(STORAGE_KEY) === 'dark'
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
    watch(isDark, (val) => {
      document.documentElement.setAttribute('data-theme', val ? 'dark' : 'light')
      localStorage.setItem(STORAGE_KEY, val ? 'dark' : 'light')
    })
  }

  return { isDark, toggle: () => { isDark.value = !isDark.value }, init }
}
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm run test -- useTheme
```

Expected: PASS (3 tests)

- [ ] **Step 5: Initialize theme early in App.vue**

Replace `frontend/src/App.vue`:

```vue
<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { init } = useTheme()
onMounted(init)
</script>
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/composables/useTheme.ts frontend/src/tests/useTheme.test.ts frontend/src/App.vue
git commit -m "feat(ui): add useTheme composable with localStorage persistence"
```

---

## Task 3: Project Store — Iteration Context

**Files:**
- Modify: `frontend/src/stores/project.ts`
- Create: `frontend/src/tests/projectStore.iteration.test.ts`

**Interfaces:**
- Produces: `currentIterationId: Ref<string | null>`, `currentIteration: Ref<any | null>`, `setCurrentIteration(it: any | null): void`, `clearCurrentIteration(): void`
- The `initFromStorage()` function must also restore `currentIterationId` from localStorage

- [ ] **Step 1: Write the failing test**

Create `frontend/src/tests/projectStore.iteration.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectStore } from '@/stores/project'

describe('projectStore — iteration context', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('currentIterationId is null by default', () => {
    const store = useProjectStore()
    expect(store.currentIterationId).toBeNull()
  })

  it('setCurrentIteration() sets the iteration and persists id', () => {
    const store = useProjectStore()
    store.setCurrentIteration({ id: 'it-1', name: 'Sprint 1' })
    expect(store.currentIterationId).toBe('it-1')
    expect(store.currentIteration?.name).toBe('Sprint 1')
    expect(localStorage.getItem('currentIterationId')).toBe('it-1')
  })

  it('setCurrentIteration(null) clears the iteration', () => {
    const store = useProjectStore()
    store.setCurrentIteration({ id: 'it-1', name: 'Sprint 1' })
    store.setCurrentIteration(null)
    expect(store.currentIterationId).toBeNull()
    expect(localStorage.getItem('currentIterationId')).toBeNull()
  })

  it('clearCurrentIteration() removes from store and localStorage', () => {
    const store = useProjectStore()
    store.setCurrentIteration({ id: 'it-1', name: 'Sprint 1' })
    store.clearCurrentIteration()
    expect(store.currentIterationId).toBeNull()
    expect(localStorage.getItem('currentIterationId')).toBeNull()
  })

  it('initFromStorage() restores currentIterationId', () => {
    localStorage.setItem('currentProjectId', 'proj-1')
    localStorage.setItem('currentIterationId', 'it-42')
    const store = useProjectStore()
    store.initFromStorage()
    expect(store.currentIterationId).toBe('it-42')
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend && npm run test -- projectStore.iteration
```

Expected: FAIL — `setCurrentIteration is not a function`

- [ ] **Step 3: Extend the project store**

Replace `frontend/src/stores/project.ts` with:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref<string | null>(null)
  const currentProject = ref<any | null>(null)
  const myProjects = ref<any[]>([])
  const currentIterationId = ref<string | null>(null)
  const currentIteration = ref<any | null>(null)

  const hasProject = computed(() => !!currentProjectId.value)

  function setCurrentProject(project: any) {
    currentProject.value = project
    currentProjectId.value = project.id
    localStorage.setItem('currentProjectId', project.id)
  }

  function clearCurrentProject() {
    currentProject.value = null
    currentProjectId.value = null
    localStorage.removeItem('currentProjectId')
  }

  function setCurrentIteration(iteration: any | null) {
    currentIteration.value = iteration
    currentIterationId.value = iteration?.id ?? null
    if (iteration?.id) {
      localStorage.setItem('currentIterationId', iteration.id)
    } else {
      localStorage.removeItem('currentIterationId')
    }
  }

  function clearCurrentIteration() {
    currentIteration.value = null
    currentIterationId.value = null
    localStorage.removeItem('currentIterationId')
  }

  async function fetchMyProjects() {
    const res = await projectsApi.getMine()
    myProjects.value = res.data
    return myProjects.value
  }

  function initFromStorage() {
    const storedProject = localStorage.getItem('currentProjectId')
    if (storedProject) currentProjectId.value = storedProject

    const storedIteration = localStorage.getItem('currentIterationId')
    if (storedIteration) currentIterationId.value = storedIteration
  }

  return {
    currentProjectId,
    currentProject,
    myProjects,
    currentIterationId,
    currentIteration,
    hasProject,
    setCurrentProject,
    clearCurrentProject,
    setCurrentIteration,
    clearCurrentIteration,
    fetchMyProjects,
    initFromStorage,
  }
})
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm run test -- projectStore.iteration
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/project.ts frontend/src/tests/projectStore.iteration.test.ts
git commit -m "feat(store): add iteration context to project store"
```

---

## Task 4: ProjectRail Component

**Files:**
- Create: `frontend/src/components/ProjectRail.vue`
- Create: `frontend/src/components/__tests__/ProjectRail.spec.ts`

**Interfaces:**
- Props: `projects: any[]`, `currentProjectId: string | null`
- Emits: `select-project(project: any)`, `create-project()`
- Consumes: CSS variables `--rail-width`, `--rail-bg`, `--topbar-height`, `--border-default`, `--bg-hover`, `--color-primary`, `--text-muted`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/__tests__/ProjectRail.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectRail from '../ProjectRail.vue'

const projects = [
  { id: '1', name: 'Alpha' },
  { id: '2', name: 'Beta' },
]
const stubs = { ElTooltip: { template: '<slot />' } }

describe('ProjectRail', () => {
  it('renders one icon per project', () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: '1' },
      global: { stubs }
    })
    expect(wrapper.findAll('.project-icon')).toHaveLength(2)
  })

  it('first letter of project name appears in each icon', () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: null },
      global: { stubs }
    })
    const icons = wrapper.findAll('.project-icon')
    expect(icons[0].text()).toBe('A')
    expect(icons[1].text()).toBe('B')
  })

  it('active project icon has .active class', () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: '1' },
      global: { stubs }
    })
    const icons = wrapper.findAll('.project-icon')
    expect(icons[0].classes()).toContain('active')
    expect(icons[1].classes()).not.toContain('active')
  })

  it('emits select-project with the project when icon is clicked', async () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: null },
      global: { stubs }
    })
    await wrapper.findAll('.project-icon')[1].trigger('click')
    expect(wrapper.emitted('select-project')?.[0]).toEqual([projects[1]])
  })

  it('emits create-project when + button is clicked', async () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: null },
      global: { stubs }
    })
    await wrapper.find('.create-btn').trigger('click')
    expect(wrapper.emitted('create-project')).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend && npm run test -- ProjectRail
```

Expected: FAIL — "Cannot find module '../ProjectRail.vue'"

- [ ] **Step 3: Implement ProjectRail.vue**

Create `frontend/src/components/ProjectRail.vue`:

```vue
<template>
  <nav class="project-rail">
    <div class="rail-logo" @click="$router.push('/projects')">
      <span class="logo-abbr">CS</span>
    </div>

    <div class="rail-projects">
      <el-tooltip
        v-for="project in projects"
        :key="project.id"
        :content="project.name"
        placement="right"
        :show-after="300"
      >
        <div
          :class="['project-icon', { active: project.id === currentProjectId }]"
          @click="$emit('select-project', project)"
        >
          {{ project.name.charAt(0).toUpperCase() }}
        </div>
      </el-tooltip>
    </div>

    <div class="rail-footer">
      <el-tooltip content="创建项目" placement="right">
        <div class="create-btn" @click="$emit('create-project')">+</div>
      </el-tooltip>
    </div>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  projects: any[]
  currentProjectId: string | null
}>()

defineEmits<{
  (e: 'select-project', project: any): void
  (e: 'create-project'): void
}>()
</script>

<style scoped>
.project-rail {
  width: var(--rail-width);
  background: var(--rail-bg);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  overflow: hidden;
}

.rail-logo {
  width: 100%;
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-default);
  cursor: pointer;
  flex-shrink: 0;
}

.logo-abbr {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 0.05em;
}

.rail-projects {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 0;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
}

.project-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: var(--bg-hover);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
  user-select: none;
}

.project-icon:hover,
.project-icon.active {
  background: var(--color-primary);
  color: #fff;
}

.rail-footer {
  padding: 0.75rem 0;
  border-top: 1px solid var(--border-default);
  width: 100%;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.create-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  border: 1.5px dashed var(--border-default);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.create-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm run test -- ProjectRail
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProjectRail.vue frontend/src/components/__tests__/ProjectRail.spec.ts
git commit -m "feat(ui): add ProjectRail component"
```

---

## Task 5: ModuleSidebar Component

**Files:**
- Create: `frontend/src/components/ModuleSidebar.vue`
- Create: `frontend/src/components/__tests__/ModuleSidebar.spec.ts`

**Interfaces:**
- Props: none (reads `projectStore.currentProject` internally)
- Emits: none (uses `router-link` for navigation)
- Consumes: `useProjectStore()`, CSS variables `--sidebar-width`, `--sidebar-bg`, `--topbar-height`, `--border-default`, `--border-light`, `--bg-hover`, `--color-primary`, `--text-primary`, `--text-secondary`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/__tests__/ModuleSidebar.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ModuleSidebar from '../ModuleSidebar.vue'

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }]
})

describe('ModuleSidebar', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders all nav groups', () => {
    const wrapper = mount(ModuleSidebar, {
      global: {
        plugins: [router],
        stubs: { ElIcon: true, ElTooltip: { template: '<slot />' } }
      }
    })
    const links = wrapper.findAll('.nav-item')
    expect(links.length).toBeGreaterThanOrEqual(8)
  })

  it('renders two dividers separating three groups', () => {
    const wrapper = mount(ModuleSidebar, {
      global: {
        plugins: [router],
        stubs: { ElIcon: true, ElTooltip: { template: '<slot />' } }
      }
    })
    expect(wrapper.findAll('.nav-divider')).toHaveLength(2)
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend && npm run test -- ModuleSidebar
```

Expected: FAIL — "Cannot find module '../ModuleSidebar.vue'"

- [ ] **Step 3: Implement ModuleSidebar.vue**

Create `frontend/src/components/ModuleSidebar.vue`:

```vue
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
      <router-link to="/standup" class="nav-item">
        <el-icon><Calendar /></el-icon>
        <span>站会</span>
      </router-link>

      <div class="nav-divider" />

      <!-- 管理 -->
      <router-link to="/users" class="nav-item">
        <el-icon><User /></el-icon>
        <span>成员</span>
      </router-link>
      <router-link to="/settings" class="nav-item">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useProjectStore } from '@/stores/project'
import {
  DataLine, Document, WarnTriangleFilled, Timer,
  Files, Calendar, User, Setting
} from '@element-plus/icons-vue'

const projectStore = useProjectStore()
const projectName = computed(() => projectStore.currentProject?.name || '未选择项目')
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
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm run test -- ModuleSidebar
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ModuleSidebar.vue frontend/src/components/__tests__/ModuleSidebar.spec.ts
git commit -m "feat(ui): add ModuleSidebar component"
```

---

## Task 6: AppTopbar Component

**Files:**
- Create: `frontend/src/components/AppTopbar.vue`
- Create: `frontend/src/components/__tests__/AppTopbar.spec.ts`

**Interfaces:**
- Props: none (reads from stores and router internally)
- Emits: none
- Consumes: `useProjectStore()` (`currentProjectId`, `currentIteration`, `setCurrentIteration()`), `useAuthStore()` (`user`, `logout()`), `useTheme()` (`isDark`, `toggle`), `iterationsApi.byProject(projectId)`
- Routes that disable the iteration selector: `/documents`, `/standup`, `/users`, `/settings`, `/mcp-config`, `/modules`, `/webhooks`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/__tests__/AppTopbar.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppTopbar from '../AppTopbar.vue'

vi.mock('@/api', () => ({
  iterationsApi: { byProject: vi.fn().mockResolvedValue({ data: [] }) }
}))
vi.mock('@/composables/useTheme', () => ({
  useTheme: () => ({ isDark: { value: false }, toggle: vi.fn(), init: vi.fn() })
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }]
})

const elStubs = {
  ElDropdown: { template: '<div><slot /><slot name="dropdown" /></div>' },
  ElDropdownMenu: { template: '<div><slot /></div>' },
  ElDropdownItem: { template: '<div><slot /></div>' },
  ElIcon: true,
}

describe('AppTopbar', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders the user avatar initial', async () => {
    const { useAuthStore } = await import('@/stores/auth')
    const auth = useAuthStore()
    auth.user = { name: 'Test User' } as any
    const wrapper = mount(AppTopbar, { global: { plugins: [router], stubs: elStubs } })
    expect(wrapper.find('.user-avatar').text()).toBe('T')
  })

  it('shows "选择迭代" placeholder when no iteration is selected', () => {
    const wrapper = mount(AppTopbar, { global: { plugins: [router], stubs: elStubs } })
    expect(wrapper.find('.iteration-label').text()).toBe('选择迭代')
  })

  it('shows current iteration name when one is selected', async () => {
    const { useProjectStore } = await import('@/stores/project')
    const store = useProjectStore()
    store.currentIteration = { id: 'it-1', name: 'Sprint 3' }
    const wrapper = mount(AppTopbar, { global: { plugins: [router], stubs: elStubs } })
    expect(wrapper.find('.iteration-label').text()).toBe('Sprint 3')
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend && npm run test -- AppTopbar
```

Expected: FAIL — "Cannot find module '../AppTopbar.vue'"

- [ ] **Step 3: Implement AppTopbar.vue**

Create `frontend/src/components/AppTopbar.vue`:

```vue
<template>
  <header class="app-topbar">
    <div class="topbar-left">
      <el-dropdown
        v-if="showIterationSelector"
        trigger="click"
        @command="onIterationSelect"
      >
        <div class="iteration-selector">
          <el-icon><Calendar /></el-icon>
          <span class="iteration-label">{{ currentIterationLabel }}</span>
          <el-icon class="arrow-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null">全部</el-dropdown-item>
            <el-dropdown-item
              v-for="it in iterations"
              :key="it.id"
              :command="it"
            >
              {{ it.name }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <div v-else class="iteration-selector disabled">
        <el-icon><Calendar /></el-icon>
        <span class="iteration-label">—</span>
      </div>

      <span v-if="breadcrumb" class="topbar-breadcrumb">{{ breadcrumb }}</span>
    </div>

    <div class="topbar-right">
      <el-icon class="topbar-action" @click="toggle">
        <Sunny v-if="isDark" />
        <Moon v-else />
      </el-icon>

      <el-dropdown trigger="click">
        <div class="user-avatar">{{ userInitial }}</div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useTheme } from '@/composables/useTheme'
import { iterationsApi } from '@/api'
import { Calendar, ArrowDown, Sunny, Moon } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectStore = useProjectStore()
const { isDark, toggle } = useTheme()

const iterations = ref<any[]>([])

const NO_ITERATION_ROUTES = [
  '/documents', '/standup', '/users', '/settings',
  '/mcp-config', '/modules', '/webhooks',
]
const showIterationSelector = computed(() =>
  !NO_ITERATION_ROUTES.some(r => route.path === r || route.path.startsWith(r + '/'))
)

const currentIterationLabel = computed(
  () => projectStore.currentIteration?.name ?? '选择迭代'
)

const BREADCRUMB_MAP: Record<string, string> = {
  '/dashboard':     '概览',
  '/requirements':  '需求管理',
  '/defects':       '缺陷管理',
  '/iterations':    '迭代管理',
  '/documents':     '文档管理',
  '/standup':       '站会',
  '/users':         '成员管理',
  '/settings':      '设置',
  '/mcp-config':    'MCP 配置',
  '/modules':       '模块管理',
  '/webhooks':      'Webhooks',
  '/projects':      '项目管理',
}

const breadcrumb = computed(() => {
  for (const [prefix, label] of Object.entries(BREADCRUMB_MAP)) {
    if (route.path === prefix || route.path.startsWith(prefix + '/')) return label
  }
  return ''
})

const userInitial = computed(
  () => (auth.user?.name || '用户').charAt(0).toUpperCase()
)

async function fetchIterations() {
  if (!projectStore.currentProjectId) return
  try {
    const res = await iterationsApi.byProject(projectStore.currentProjectId)
    iterations.value = res.data
  } catch { /* silently ignore */ }
}

function onIterationSelect(it: any | null) {
  projectStore.setCurrentIteration(it)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

watch(() => projectStore.currentProjectId, fetchIterations)
onMounted(fetchIterations)
</script>

<style scoped>
.app-topbar {
  height: var(--topbar-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 clamp(12px, 1.5vw, 24px);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.iteration-selector {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-btn);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-primary);
  white-space: nowrap;
  transition: background 0.15s;
  user-select: none;
}

.iteration-selector:not(.disabled):hover {
  background: var(--bg-hover);
}

.iteration-selector.disabled {
  color: var(--text-muted);
  cursor: default;
}

.iteration-label {
  max-width: 16ch;
  overflow: hidden;
  text-overflow: ellipsis;
}

.arrow-icon {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.topbar-breadcrumb {
  font-size: 0.875rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.topbar-action {
  font-size: 1.125rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.375rem;
  border-radius: var(--radius-btn);
  transition: background 0.15s, color 0.15s;
}

.topbar-action:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.user-avatar {
  width: 1.75rem;
  height: 1.75rem;
  background: var(--color-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;
}
</style>
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm run test -- AppTopbar
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/AppTopbar.vue frontend/src/components/__tests__/AppTopbar.spec.ts
git commit -m "feat(ui): add AppTopbar with iteration selector and dark mode toggle"
```

---

## Task 7: Layout.vue Refactor

**Files:**
- Modify: `frontend/src/components/Layout.vue`

**Interfaces:**
- Consumes: `ProjectRail` (emits `select-project`, `create-project`), `ModuleSidebar`, `AppTopbar`, `useProjectStore()`
- Produces: three-column shell — Rail + Sidebar + (Topbar + router-view)

- [ ] **Step 1: Replace Layout.vue**

Overwrite `frontend/src/components/Layout.vue`:

```vue
<template>
  <div class="app-shell">
    <ProjectRail
      :projects="projectStore.myProjects"
      :current-project-id="projectStore.currentProjectId"
      @select-project="onSelectProject"
      @create-project="router.push('/projects')"
    />
    <ModuleSidebar />
    <div class="main-area">
      <AppTopbar />
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import ProjectRail from '@/components/ProjectRail.vue'
import ModuleSidebar from '@/components/ModuleSidebar.vue'
import AppTopbar from '@/components/AppTopbar.vue'

const router = useRouter()
const projectStore = useProjectStore()

onMounted(async () => {
  await projectStore.fetchMyProjects()
})

function onSelectProject(project: any) {
  projectStore.setCurrentProject(project)
  router.push('/dashboard')
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-base);
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: clamp(16px, 2vw, 28px);
  background: var(--bg-base);
}
</style>
```

- [ ] **Step 2: Run the dev server and verify the layout**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 and confirm:
- Three-column layout is visible (Rail | Sidebar | Content)
- Project Rail shows project icons
- Module Sidebar shows navigation links with active state
- Topbar shows iteration selector + user avatar
- Existing pages (Requirements, Dashboard, etc.) still render correctly inside the content area

- [ ] **Step 3: Run full test suite to catch regressions**

```bash
cd frontend && npm run test
```

Expected: all previously passing tests still pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.vue
git commit -m "refactor(ui): rewrite Layout to three-column TAPD-style shell"
```

---

## Task 8: IterationDetail — Info Header + Sub-Tabs

**Files:**
- Modify: `frontend/src/views/IterationDetail.vue`

**Interfaces:**
- Consumes: existing `iterationsApi.get()`, `iterationsApi.statistics()`, `requirementsApi.byIteration()`
- Produces: page with a fixed info header (name, dates, status tag, progress bar) and four internal tabs (概览 / 需求 / 缺陷 / 成员); 概览 tab contains existing stat cards + distribution bar; 需求 tab contains existing requirements table; 缺陷 and 成员 tabs show `el-empty` placeholder

- [ ] **Step 1: Rewrite IterationDetail.vue**

Replace `frontend/src/views/IterationDetail.vue`:

```vue
<template>
  <div class="iteration-detail" v-if="iteration">
    <!-- ── Info header ─────────────────────────────────────── -->
    <div class="detail-header">
      <div class="header-main">
        <div class="header-title-row">
          <h1 class="detail-title">{{ iteration.name }}</h1>
          <el-tag :type="statusType(iteration.status)" size="large">
            {{ statusText(iteration.status) }}
          </el-tag>
        </div>
        <div class="header-meta">
          <span>{{ formatDate(iteration.planned_release_date) }}</span>
          <span class="meta-sep">→</span>
          <span>{{ iteration.actual_release_date ? formatDate(iteration.actual_release_date) : '进行中' }}</span>
        </div>
      </div>

      <div class="header-progress">
        <div class="progress-label">
          <span class="progress-pct">{{ stats.progress_pct || 0 }}%</span>
          <span class="progress-sub">{{ stats.completed || 0 }} / {{ stats.total_requirements || 0 }} 完成</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (stats.progress_pct || 0) + '%' }"
          />
        </div>
      </div>

      <el-button
        v-if="iteration.status !== 'released' && iteration.status !== 'archived'"
        type="primary"
        size="small"
        :loading="releasing"
        @click="releaseIteration"
      >
        发布迭代
      </el-button>
    </div>

    <!-- ── Sub-tabs ───────────────────────────────────────── -->
    <div class="detail-tabs">
      <span
        v-for="tab in TABS"
        :key="tab.key"
        :class="['detail-tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </span>
    </div>

    <div v-if="loading" class="tab-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <template v-else>
      <!-- 概览 -->
      <div v-show="activeTab === 'overview'">
        <el-row :gutter="14" style="margin-bottom: 1rem;">
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon blue">◇</div>
                <div><div class="stat-value">{{ stats.total_requirements || 0 }}</div><div class="stat-label">总需求</div></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon green">✓</div>
                <div><div class="stat-value">{{ stats.completed || 0 }}</div><div class="stat-label">已完成</div></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon amber">↻</div>
                <div><div class="stat-value">{{ stats.in_progress || 0 }}</div><div class="stat-label">进行中</div></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon purple">%</div>
                <div><div class="stat-value">{{ stats.progress_pct || 0 }}%</div><div class="stat-label">完成率</div></div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="never">
          <template #header><span class="card-title">状态分布</span></template>
          <div class="dist-bar">
            <div
              v-for="(count, status) in stats.status_distribution || {}"
              :key="status"
              :class="['dist-segment', status]"
              :style="{ width: ((count / (stats.total_requirements || 1)) * 100) + '%' }"
              :title="`${reqStatusText(status as string)}: ${count}`"
            />
          </div>
          <div class="dist-legend">
            <div v-for="(count, status) in stats.status_distribution || {}" :key="status" class="legend-item">
              <span :class="['dist-dot', status]" />
              <span>{{ reqStatusText(status as string) }} · {{ count }}</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 需求 -->
      <div v-show="activeTab === 'requirements'">
        <el-card shadow="never" body-style="padding:0;">
          <template #header>
            <span class="card-title">迭代需求 ({{ requirements.length }})</span>
          </template>
          <el-table :data="requirements" stripe style="width:100%">
            <el-table-column prop="title" label="需求" min-width="240">
              <template #default="{ row }">
                <el-link type="primary" underline="never" @click="$router.push(`/requirement/${row.id}`)">
                  {{ row.title }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }">
                <el-tag :type="priorityType(row.priority)" size="small" effect="plain">{{ row.priority }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="reqStatusType(row.status)" size="small">{{ reqStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="assignee_id" label="指派给" width="120">
              <template #default="{ row }">
                <span class="text-muted text-small">{{ row.assignee_id ? row.assignee_id.slice(0, 8) : '未指派' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止日期" width="120">
              <template #default="{ row }">
                <span class="text-muted text-small">{{ row.due_date ? formatDate(row.due_date) : '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <!-- 缺陷 -->
      <div v-show="activeTab === 'defects'">
        <el-empty description="缺陷视图待开发" />
      </div>

      <!-- 成员 -->
      <div v-show="activeTab === 'members'">
        <el-empty description="成员视图待开发" />
      </div>
    </template>
  </div>

  <div v-else-if="loading">
    <el-skeleton :rows="6" animated />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { iterationsApi, requirementsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const iteration = ref<any>(null)
const requirements = ref<any[]>([])
const stats = ref<any>({})
const loading = ref(false)
const releasing = ref(false)
const activeTab = ref<'overview' | 'requirements' | 'defects' | 'members'>('overview')

const TABS = [
  { key: 'overview',      label: '概览' },
  { key: 'requirements',  label: '需求' },
  { key: 'defects',       label: '缺陷' },
  { key: 'members',       label: '成员' },
] as const

const statusType = (s: string) => ({
  planning: 'info', development: 'primary', testing: 'warning',
  released: 'success', archived: 'info',
}[s] || 'info')

const statusText = (s: string) => ({
  planning: '规划中', development: '开发中', testing: '测试中',
  released: '已发布', archived: '已归档',
}[s] || s)

const reqStatusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success',
  review_rejected: 'danger', completed: 'success',
}[s] || 'info')

const reqStatusText = (s: string) => ({
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const priorityType = (p: string) =>
  ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')

const formatDate = (d: string) =>
  d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const releaseIteration = async () => {
  try {
    await ElMessageBox.confirm(
      '发布迭代将归档所有该迭代下需求的草稿文档，无法撤销。确认发布？',
      '提示', { type: 'warning' }
    )
    releasing.value = true
    const res = await iterationsApi.release(route.params.id as string)
    if (res.data.success) {
      ElMessage.success(`发布成功。归档了 ${res.data.archived_documents} 份文档。`)
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  } finally {
    releasing.value = false
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [itRes, rRes, sRes] = await Promise.all([
      iterationsApi.get(route.params.id as string),
      requirementsApi.byIteration(route.params.id as string),
      iterationsApi.statistics(route.params.id as string),
    ])
    iteration.value = itRes.data
    requirements.value = rRes.data
    stats.value = sRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.iteration-detail { display: flex; flex-direction: column; gap: 1rem; }

/* Info header */
.detail-header {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-card);
  padding: clamp(12px, 1.5vw, 20px);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.header-main { flex: 1; min-width: 0; }

.header-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.375rem;
  flex-wrap: wrap;
}

.detail-title {
  font-size: clamp(1rem, 1.5vw, 1.375rem);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.meta-sep { color: var(--text-muted); }

/* Progress */
.header-progress { width: clamp(140px, 20vw, 220px); }

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.375rem;
}

.progress-pct { font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.progress-sub { font-size: 0.75rem; color: var(--text-muted); }

.progress-bar {
  height: 6px;
  background: var(--border-default);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.4s ease;
}

/* Tabs */
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-default);
}

.detail-tab {
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
  user-select: none;
}

.detail-tab:hover { color: var(--text-primary); }
.detail-tab.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 500; }

.tab-loading { margin-top: 1rem; }

/* Stat cards */
.stat-cell { display: flex; align-items: center; gap: 0.875rem; }
.stat-value { font-size: 1.375rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 3px; }
.stat-icon {
  width: 2.5rem; height: 2.5rem; border-radius: 0.625rem;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.125rem; flex-shrink: 0;
}
.stat-icon.blue   { background: rgba(45,91,255,0.1); }
.stat-icon.green  { background: rgba(0,168,112,0.1); }
.stat-icon.amber  { background: rgba(255,154,46,0.1); }
.stat-icon.purple { background: rgba(139,92,246,0.1); }

/* Distribution bar */
.dist-bar {
  display: flex; height: 8px; border-radius: 4px;
  overflow: hidden; background: var(--border-light); margin-bottom: 0.875rem;
}
.dist-segment { height: 100%; transition: width 0.3s; }
.dist-segment.completed      { background: #10b981; }
.dist-segment.in_progress    { background: #f59e0b; }
.dist-segment.pending_review { background: #ec4899; }
.dist-segment.assigned       { background: #6366f1; }
.dist-segment.review_approved{ background: #06b6d4; }
.dist-segment.draft          { background: #9ca3af; }

.dist-legend { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.legend-item { display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: var(--text-secondary); }
.dist-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.dist-dot.completed      { background: #10b981; }
.dist-dot.in_progress    { background: #f59e0b; }
.dist-dot.pending_review { background: #ec4899; }
.dist-dot.assigned       { background: #6366f1; }
.dist-dot.review_approved{ background: #06b6d4; }
.dist-dot.draft          { background: #9ca3af; }
</style>
```

- [ ] **Step 2: Start dev server and manually verify the iteration detail page**

```bash
cd frontend && npm run dev
```

Navigate to an iteration detail page (`/iteration/<id>`):
- Confirm the info header shows name, date range, status tag, and progress bar
- Confirm sub-tabs render and switching between them works
- Confirm the 概览 tab shows stat cards and distribution bar
- Confirm the 需求 tab shows the requirements table
- Confirm 缺陷 and 成员 tabs show the `el-empty` placeholder

- [ ] **Step 3: Run full test suite**

```bash
cd frontend && npm run test
```

Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/IterationDetail.vue
git commit -m "refactor(ui): add info header and sub-tabs to IterationDetail"
```
