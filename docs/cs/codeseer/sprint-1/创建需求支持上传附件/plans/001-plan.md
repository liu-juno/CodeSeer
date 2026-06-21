# 创建需求改为独立页面 - 实现计划

## Global Constraints

- Vue 3 Composition API
- TypeScript strict mode
- Element Plus 组件库
- 前端项目路径: `frontend/`

---

## Task 1: 创建 RequirementCreate.vue 页面

**Files:**
- Create: `frontend/src/views/RequirementCreate.vue`
- Test: `frontend/src/views/__tests__/RequirementCreate.spec.ts`

**Interfaces:**
- Consumes: `VditorEditor`, `attachmentsApi`
- Produces: 独立创建需求页面

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/views/__tests__/RequirementCreate.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import RequirementCreate from '../RequirementCreate.vue'

describe('RequirementCreate', () => {
  it('should render create page with steps', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/requirement/new', component: RequirementCreate }]
    })
    router.push('/requirement/new')
    await router.isReady()
    const wrapper = mount(RequirementCreate, {
      global: { plugins: [router] }
    })
    expect(wrapper.find('.page-title').text()).toBe('创建需求')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm run test -- --run src/views/__tests__/RequirementCreate.spec.ts 2>&1
```
预期: FAIL (文件不存在)

- [ ] **Step 3: 写最小实现**

创建 `frontend/src/views/RequirementCreate.vue`，包含：
- 页面标题"创建需求"
- el-steps 3步向导
- 3个步骤的表单内容
- VditorEditor 用于描述
- el-upload 用于附件
- 底部操作按钮

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm run test -- --run src/views/__tests__/RequirementCreate.spec.ts 2>&1
```
预期: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/RequirementCreate.vue
git commit -m "feat: add RequirementCreate page for requirement creation"
```

---

## Task 2: 添加路由配置

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 添加路由**

```typescript
{
  path: 'requirement/new',
  name: 'requirement-create',
  component: () => import('@/views/RequirementCreate.vue')
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: add route for /requirement/new"
```

---

## Task 3: 修改 Requirements.vue 移除弹窗

**Files:**
- Modify: `frontend/src/views/Requirements.vue`

- [ ] **Step 1: 移除弹窗相关代码**

1. 移除 `showWizard` ref
2. 移除 `currentStep` ref
3. 移除 `submitting` ref
4. 移除 `openWizard` 函数
5. 移除 `submitRequirement` 函数
6. 移除 `form` ref 和 `defaultForm`
7. 移除 `steps` 定义
8. 移除 `canNext` computed
9. 移除 `uploadRef`, `onFileChange`, `removeFile`
10. 移除 `DESCRIPTION_TEMPLATE`
11. 移除整个 `<el-dialog>` 弹窗代码块
12. 修改"创建需求"按钮为路由跳转

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Requirements.vue
git commit -m "refactor: remove create requirement dialog, use dedicated page"
```

---

## Task 4: 添加 TypeScript 类型定义

**Files:**
- Modify: `frontend/src/types/requirement.ts` (如不存在则创建)

- [ ] **Step 1: 添加类型定义**

```typescript
export interface RequirementFormData {
  title: string
  project_id: string
  iteration_id?: string
  description: string
  criteriaList: string[]
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  due_date?: string
  uploadedFiles: File[]
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/types/requirement.ts
git commit -m "types: add RequirementFormData interface"
```

---

## 验收检查清单

- [ ] Task 1: RequirementCreate.vue 页面存在且测试通过
- [ ] Task 2: 路由 `/requirement/new` 已添加
- [ ] Task 3: Requirements.vue 弹窗已移除，按钮改为路由跳转
- [ ] Task 4: TypeScript 类型定义已添加
- [ ] 页面可以正常打开
- [ ] 创建需求流程完整可用