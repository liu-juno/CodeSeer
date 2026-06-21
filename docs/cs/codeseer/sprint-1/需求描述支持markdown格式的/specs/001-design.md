# 需求描述支持 Markdown 格式 - 设计文档

## 1. 概述

本需求为 CodeSeer 项目添加 Markdown 编辑和展示功能，使需求描述支持 Markdown 格式，并提供富文本编辑体验。

## 2. 技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| **编辑器** | `vditor` v3.x | 功能丰富、支持实时预览、完整引入 |
| **Markdown 解析** | `marked` | 详情页渲染 Markdown 为 HTML |
| **编辑器引入方式** | 完整引入 | 约 150-200KB，配置简单 |

## 3. 组件设计

### 3.1 VditorEditor.vue

Markdown 编辑器封装组件。

**位置**: `frontend/src/components/VditorEditor.vue`

**Props**:
- `modelValue: string` - Markdown 内容
- `placeholder?: string` - 占位文本
- `height?: string` - 高度（默认 300px）

**Events**:
- `update:modelValue` - 内容变化时触发

**功能**:
- 工具栏：标题、粗体、斜体、代码、列表、链接等
- 支持实时预览模式
- 输出纯 Markdown 源码

### 3.2 MarkdownRenderer.vue

Markdown 渲染+源码切换展示组件。

**位置**: `frontend/src/components/MarkdownRenderer.vue`

**Props**:
- `content: string` - Markdown 源码
- `height?: string` - 高度（默认 200px）

**功能**:
- 默认 Tab 显示渲染后的 HTML
- "源码" Tab 显示原始 Markdown
- 使用 `marked` 库进行渲染

## 4. 修改点

### 4.1 Requirements.vue

**文件**: `frontend/src/views/Requirements.vue`

**修改**:
1. 引入 `VditorEditor.vue` 组件
2. 在"需求内容"步骤中，用 `<VditorEditor>` 替换 `<el-input type="textarea">`
3. 保留其他步骤逻辑不变

**修改前**:
```vue
<el-input
  v-model="requirementForm.description"
  type="textarea"
  :rows="8"
  placeholder="请输入需求描述"
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

### 4.2 RequirementDetail.vue

**文件**: `frontend/src/views/RequirementDetail.vue`

**修改**:
1. 引入 `MarkdownRenderer.vue` 组件
2. 用 `<MarkdownRenderer :content="requirement.description" />` 替换纯文本展示

**修改前**:
```vue
<el-descriptions-item label="描述">
  {{ requirement.description || '-' }}
</el-descriptions-item>
```

**修改后**:
```vue
<el-descriptions-item label="描述">
  <MarkdownRenderer :content="requirement.description" />
</el-descriptions-item>
```

### 4.3 package.json

**文件**: `frontend/package.json`

**新增依赖**:
```json
{
  "vditor": "^3.10.0",
  "marked": "^12.0.0"
}
```

### 4.4 main.ts（如需要全局注册）

**文件**: `frontend/src/main.ts`

如需全局注册组件，添加：
```typescript
import VditorEditor from './components/VditorEditor.vue'
import MarkdownRenderer from './components/MarkdownRenderer.vue'

app.component('VditorEditor', VditorEditor)
app.component('MarkdownRenderer', MarkdownRenderer)
```

## 5. 用户交互流程

### 5.1 创建/编辑需求

1. 用户点击"创建需求"按钮
2. 弹出 3 步向导对话框
3. 步骤一：填写基础信息（名称、优先级、负责人等）
4. 步骤二：填写需求内容，显示 Vditor 编辑器
   - 用户可使用工具栏格式化文本
   - 支持实时预览 Markdown 效果
5. 步骤三：设置（标签等）
6. 点击"确定"提交，保存 Markdown 源码到后端

### 5.2 查看需求详情

1. 用户点击需求进入详情页
2. 默认显示渲染后的 HTML（标题、列表、代码块等样式）
3. 提供"源码"Tab，可切换查看原始 Markdown 内容

## 6. 数据存储

- `requirement.description` 字段存储 Markdown 源码（字符串）
- 渲染在展示时由前端完成（使用 `marked` 库）
- 后端无需修改数据模型

## 7. 验收标准

1. ✅ 创建需求时，描述字段使用 Vditor 编辑器
2. ✅ 编辑器支持工具栏（标题、粗体、斜体、代码、列表等）
3. ✅ 编辑器支持实时预览 Markdown 效果
4. ✅ 需求详情页默认显示渲染后的 HTML
5. ✅ 详情页支持切换到源码视图查看原始 Markdown
6. ✅ 依赖包 `vditor` 和 `marked` 已添加到 package.json

## 8. 风险与注意事项

1. **SSR 兼容性**: Vditor 仅支持客户端渲染，确保组件在客户端挂载
2. **XSS 防护**: marked 默认不防止 XSS，需配置 `marked.use({ renderer })` 或使用 `DOMPurify` 净化 HTML
3. **包体积**: 完整引入 vditor 约 150-200KB，需评估对首屏加载的影响