# 需求描述支持 Markdown 格式 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为需求描述添加 Markdown 编辑和展示功能，使用 vditor 作为编辑器，marked 作为渲染库。

**Architecture:** 通过新增两个 Vue 组件（VditorEditor 和 MarkdownRenderer）实现编辑和展示功能，修改现有 Requirements.vue 和 RequirementDetail.vue 引用新组件。

**Tech Stack:** Vue 3, TypeScript, Element Plus, vditor ^3.10.0, marked ^12.0.0

## Global Constraints

- Vue 3 Composition API
- TypeScript strict mode
- Element Plus 组件库
- 前端项目路径: `frontend/`

---

## Task 1: 安装依赖 vditor 和 marked

**Files:**
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: -
- Produces: `node_modules/vditor`, `node_modules/marked`

- [ ] **Step 1: Write失败的测试（验证依赖未安装）**

```bash
cd frontend && npm list vditor marked 2>&1 | grep -q "vditor" || echo "vditor not found"
echo $?
```
预期输出: `1` (因为未安装)

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm list vditor marked 2>&1
```
预期: command returns non-zero 或输出显示未找到

- [ ] **Step 3: 安装依赖**

```bash
cd frontend && npm install vditor@^3.10.0 marked@^12.0.0
```

- [ ] **Step 4: 运行测试确认成功**

```bash
cd frontend && npm list vditor marked
```
预期输出包含 vditor 和 marked 版本信息

- [ ] **Step 5: 提交**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add vditor and marked for markdown support"
```

---

## Task 2: 创建 VditorEditor.vue 组件

**Files:**
- Create: `frontend/src/components/VditorEditor.vue`
- Test: `frontend/src/components/__tests__/VditorEditor.spec.ts`

**Interfaces:**
- Consumes: -
- Produces: `<VditorEditor>` 组件，props: `modelValue: string`, `placeholder?: string`, `height?: string`; events: `update:modelValue`

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/components/__tests__/VditorEditor.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import VditorEditor from '../VditorEditor.vue'

describe('VditorEditor', () => {
  it('should render editor with initial value', () => {
    const wrapper = mount(VditorEditor, {
      props: { modelValue: '# Hello Markdown' }
    })
    expect(wrapper.find('.vditor').exists()).toBe(true)
  })

  it('should emit update:modelValue on change', async () => {
    const wrapper = mount(VditorEditor, {
      props: { modelValue: '' }
    })
    // Simulate vditor content change
    const vm = wrapper.vm as any
    vm.handleValueChanged('# New Content')
    await wrapper.flush()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['# New Content'])
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm run test -- --run src/components/__tests__/VditorEditor.spec.ts 2>&1
```
预期: FAIL (VditorEditor.vue 不存在)

- [ ] **Step 3: 写最小实现**

```vue
<!-- frontend/src/components/VditorEditor.vue -->
<template>
  <div ref="editorRef" class="vditor-editor"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  height?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorRef = ref<HTMLElement>()
let vditor: Vditor | null = null

const handleValueChanged = (value: string) => {
  emit('update:modelValue', value)
}

onMounted(() => {
  vditor = new Vditor(editorRef.value!, {
    value: props.modelValue,
    placeholder: props.placeholder || '',
    height: parseInt(props.height || '300'),
    mode: 'wysiwyg',
    after: () => {
      vditor!.getElement().addEventListener('input', () => {
        handleValueChanged(vditor!.getValue())
      })
    }
  })
})

onBeforeUnmount(() => {
  vditor?.destroy()
})

watch(() => props.modelValue, (newVal) => {
  if (vditor && vditor.getValue() !== newVal) {
    vditor.setValue(newVal)
  }
})
</script>

<style scoped>
.vditor-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm run test -- --run src/components/__tests__/VditorEditor.spec.ts 2>&1
```
预期: PASS

- [ ] **Step 5: 重构检查**
- 确认 Vditor 实例正确销毁（onBeforeUnmount）
- 确认 watch 正确处理外部 modelValue 变化

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/VditorEditor.vue frontend/src/components/__tests__/VditorEditor.spec.ts
git commit -m "feat: add VditorEditor component for markdown editing"
```

---

## Task 3: 创建 MarkdownRenderer.vue 组件

**Files:**
- Create: `frontend/src/components/MarkdownRenderer.vue`
- Test: `frontend/src/components/__tests__/MarkdownRenderer.spec.ts`

**Interfaces:**
- Consumes: -
- Produces: `<MarkdownRenderer>` 组件，props: `content: string`, `height?: string`; 提供 Tab 切换：渲染视图 / 原始 Markdown

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/components/__tests__/MarkdownRenderer.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownRenderer from '../MarkdownRenderer.vue'

describe('MarkdownRenderer', () => {
  it('should render markdown as HTML', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '# Hello\n\nThis is **bold** text' }
    })
    expect(wrapper.find('.markdown-body h1').text()).toBe('Hello')
    expect(wrapper.find('.markdown-body strong').text()).toBe('bold')
  })

  it('should show source tab with raw markdown', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '# Test' }
    })
    // Click source tab
    const tabs = wrapper.findAll('.el-tabs__item')
    expect(tabs.length).toBeGreaterThan(1)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm run test -- --run src/components/__tests__/MarkdownRenderer.spec.ts 2>&1
```
预期: FAIL (MarkdownRenderer.vue 不存在)

- [ ] **Step 3: 写最小实现**

```vue
<!-- frontend/src/components/MarkdownRenderer.vue -->
<template>
  <el-tabs v-model="activeTab" class="markdown-renderer">
    <el-tab-pane label="预览" name="preview">
      <div
        class="markdown-body"
        v-html="renderedHtml"
        :style="{ maxHeight: height || '300px', overflow: 'auto' }"
      ></div>
    </el-tab-pane>
    <el-tab-pane label="源码" name="source">
      <pre
        class="source-code"
        :style="{ maxHeight: height || '300px', overflow: 'auto' }"
      >{{ content }}</pre>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
  height?: string
}>()

const activeTab = ref('preview')

const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked(props.content)
})
</script>

<style scoped>
.markdown-body {
  padding: 16px;
  line-height: 1.6;
}

.markdown-body :deep(h1) { font-size: 1.5em; margin: 0.5em 0; }
.markdown-body :deep(h2) { font-size: 1.3em; margin: 0.5em 0; }
.markdown-body :deep(h3) { font-size: 1.1em; margin: 0.5em 0; }
.markdown-body :deep(p) { margin: 0.5em 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.5em; margin: 0.5em 0; }
.markdown-body :deep(code) { background: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; }
.markdown-body :deep(pre) { background: #f5f5f5; padding: 1em; overflow: auto; border-radius: 4px; }

.source-code {
  margin: 0;
  padding: 16px;
  background: #f5f5f5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm run test -- --run src/components/__tests__/MarkdownRenderer.spec.ts 2>&1
```
预期: PASS

- [ ] **Step 5: 重构检查**
- marked 配置为 XSS 安全（后续 Task 6 会添加 DOMPurify）
- Tab 默认选中预览

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/MarkdownRenderer.vue frontend/src/components/__tests__/MarkdownRenderer.spec.ts
git commit -m "feat: add MarkdownRenderer component with tab switch"
```

---

## Task 4: 修改 Requirements.vue 使用 VditorEditor

**Files:**
- Modify: `frontend/src/views/Requirements.vue:140-150`

**Interfaces:**
- Consumes: `<VditorEditor>` 组件
- Produces: 创建需求对话框中使用 VditorEditor 替代 textarea

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/views/__tests__/Requirements.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import Requirements from '../Requirements.vue'
import VditorEditor from '@/components/VditorEditor.vue'

describe('Requirements', () => {
  it('should use VditorEditor for description field', async () => {
    const wrapper = mount(Requirements, {
      global: {
        plugins: [createTestingPinia()],
        stubs: { VditorEditor }
      }
    })
    // Trigger create dialog
    await wrapper.find('button:contains("创建需求")').trigger('click')
    await wrapper.find('.el-button--primary').trigger('click') // Next to step 2
    expect(wrapper.findComponent(VditorEditor).exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm run test -- --run src/views/__tests__/Requirements.spec.ts 2>&1
```
预期: FAIL (VditorEditor 未被使用)

- [ ] **Step 3: 写最小实现**

在 `frontend/src/views/Requirements.vue` 中：

1. 添加 import:
```typescript
import VditorEditor from '@/components/VditorEditor.vue'
```

2. 替换 textarea（第 140-150 行附近）:
**修改前**:
```vue
<el-input
  v-model="requirementForm.description"
  type="textarea"
  :rows="8"
  placeholder="请输入需求描述，支持 Markdown 格式"
/>
```

**修改后**:
```vue
<VditorEditor
  v-model="requirementForm.description"
  placeholder="请输入需求描述，支持 Markdown 格式"
  height="300px"
/>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm run test -- --run src/views/__tests__/Requirements.spec.ts 2>&1
```
预期: PASS

- [ ] **Step 5: 手动验证**
```bash
cd frontend && npm run dev
```
打开创建需求对话框，确认描述字段使用 Vditor 编辑器

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/Requirements.vue
git commit -m "feat: replace textarea with VditorEditor in Requirements form"
```

---

## Task 5: 修改 RequirementDetail.vue 使用 MarkdownRenderer

**Files:**
- Modify: `frontend/src/views/RequirementDetail.vue:70-80`

**Interfaces:**
- Consumes: `<MarkdownRenderer>` 组件
- Produces: 需求详情页使用 MarkdownRenderer 展示描述

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/views/__tests__/RequirementDetail.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RequirementDetail from '../RequirementDetail.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

describe('RequirementDetail', () => {
  it('should use MarkdownRenderer for description', () => {
    const wrapper = mount(RequirementDetail, {
      props: {
        requirement: { id: '1', description: '# Test\n\nContent' }
      },
      global: {
        stubs: { MarkdownRenderer }
      }
    })
    expect(wrapper.findComponent(MarkdownRenderer).exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm run test -- --run src/views/__tests__/RequirementDetail.spec.ts 2>&1
```
预期: FAIL (MarkdownRenderer 未被使用)

- [ ] **Step 3: 写最小实现**

在 `frontend/src/views/RequirementDetail.vue` 中：

1. 添加 import:
```typescript
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
```

2. 替换描述展示（第 70-80 行附近）:
**修改前**:
```vue
<el-descriptions-item label="描述">
  {{ requirement.description || '-' }}
</el-descriptions-item>
```

**修改后**:
```vue
<el-descriptions-item label="描述">
  <MarkdownRenderer
    v-if="requirement.description"
    :content="requirement.description"
  />
  <span v-else>-</span>
</el-descriptions-item>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm run test -- --run src/views/__tests__/RequirementDetail.spec.ts 2>&1
```
预期: PASS

- [ ] **Step 5: 手动验证**
```bash
cd frontend && npm run dev
```
进入需求详情页，确认描述字段使用 Tab 切换渲染/源码视图

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/RequirementDetail.vue
git commit -m "feat: use MarkdownRenderer in RequirementDetail for description display"
```

---

## Task 6: XSS 安全防护（可选但推荐）

**Files:**
- Modify: `frontend/src/components/MarkdownRenderer.vue`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: DOMPurify
- Produces: MarkdownRenderer 使用 DOMPurify 净化 HTML 输出

- [ ] **Step 1: 安装 DOMPurify**

```bash
cd frontend && npm install dompurify @types/dompurify
```

- [ ] **Step 2: 修改 MarkdownRenderer 使用 DOMPurify**

**修改**:
```typescript
import DOMPurify from 'dompurify'

const renderedHtml = computed(() => {
  if (!props.content) return ''
  const rawHtml = marked(props.content)
  return DOMPurify.sanitize(rawHtml)
})
```

- [ ] **Step 3: 提交**

```bash
git add frontend/package.json frontend/src/components/MarkdownRenderer.vue
git commit -m "security: add DOMPurify to prevent XSS in markdown rendering"
```

---

## 验收检查清单

- [ ] Task 1: `vditor` 和 `marked` 已添加到 package.json
- [ ] Task 2: `VditorEditor.vue` 组件存在且测试通过
- [ ] Task 3: `MarkdownRenderer.vue` 组件存在且测试通过，支持 Tab 切换
- [ ] Task 4: `Requirements.vue` 使用 `VditorEditor` 替代 textarea
- [ ] Task 5: `RequirementDetail.vue` 使用 `MarkdownRenderer` 展示描述
- [ ] Task 6: XSS 防护已添加（DOMPurify）
- [ ] 所有测试通过 `npm run test -- --run`
- [ ] 应用可正常运行 `npm run dev`