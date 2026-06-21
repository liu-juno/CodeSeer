# 创建需求改为独立页面 - 设计文档

## 1. 概述

将创建需求从弹窗改为独立页面，提供更大的空间用于填写需求信息，提升 Markdown 编辑器和附件上传的体验。

## 2. 设计变更

### 2.1 新增页面

**文件**: `frontend/src/views/RequirementCreate.vue`

### 2.2 新增路由

**文件**: `frontend/src/router/index.ts`

```typescript
{
  path: 'requirement/new',
  name: 'requirement-create',
  component: () => import('@/views/RequirementCreate.vue')
}
```

### 2.3 修改 Requirements.vue

- 移除创建需求的弹窗 wizard
- "创建需求"按钮改为路由跳转：`$router.push('/requirement/new')`

## 3. 页面布局

```
/requirement/new (独立页面)
├── 页面标题：创建需求
├── 步骤指示器（水平 el-steps）
├── 表单内容区
│   ├── Step 1: 基础信息（标题、项目、迭代）
│   ├── Step 2: 需求内容（Markdown 编辑器 + 验收标准 + 附件上传）
│   └── Step 3: 设置（优先级、截止日期）
└── 底部操作按钮（取消 / 上一步 / 下一步 / 创建需求）
```

## 4. 表单数据模型

```typescript
interface RequirementFormData {
  title: string           // 需求标题
  project_id: string      // 所属项目 (必填)
  iteration_id: string    // 关联迭代
  description: string     // Markdown 描述
  criteriaList: string[]  // 验收标准
  priority: 'P0' | 'P1' | 'P2' | 'P3'  // 优先级
  due_date: string        // 截止日期
  uploadedFiles: File[]   // 附件
}
```

## 5. 用户交互流程

1. 用户点击"创建需求"按钮
2. 跳转到 `/requirement/new` 页面
3. 填写 Step 1 基础信息 → 点击"下一步"
4. 填写 Step 2 需求内容（Markdown 编辑器、验收标准、附件上传）→ 点击"下一步"
5. 填写 Step 3 设置（优先级、截止日期）→ 点击"创建需求"
6. 提交成功后跳转到需求详情页

## 6. 验收标准

- [ ] 创建需求使用独立页面而非弹窗
- [ ] 页面路径为 `/requirement/new`
- [ ] 表单保持 3 步向导结构
- [ ] Markdown 编辑器空间充足
- [ ] 附件上传功能正常工作
- [ ] 创建成功后跳转到需求详情页