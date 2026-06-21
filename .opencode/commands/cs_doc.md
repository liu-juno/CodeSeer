---
description: 将文档上传到 CodeSeer 平台。用法：/cs_doc [design|plan|api|other]
---

## 参数说明

支持的文档类型参数：
- `design` / `设计文档` — 需求设计文档（brainstorming 产出）
- `plan` / `计划文档` — 实现计划文档（writing-plans 产出）
- `api` / `API文档` — 接口文档
- `other` / `其他` — 其他类型文档

## 执行步骤

### 第 1 步：确认文档类型

**如果用户已传入参数**（如 `/cs_doc design`），直接使用该类型，跳到第 2 步。

**如果没有传入参数**，向用户展示选择菜单：

```
请选择要上传的文档类型：
  1. 设计文档（design）  — brainstorming 产出的需求设计
  2. 计划文档（plan）    — writing-plans 产出的实现计划
  3. API 文档（api）     — 接口说明文档
  4. 其他（other）
```

等待用户选择后继续。

### 第 2 步：确认需求

询问（或从上下文获取）要关联的需求 ID：
- 如果用户不知道 ID，调用 `list_my_requirements` 展示列表让用户选择

### 第 3 步：确认文档内容

根据文档类型给出对应的默认查找路径提示（路径格式：`docs/cs/<项目标识符>/<迭代名>/<需求名>/`）：
- `design` → `docs/cs/<项目标识符>/<迭代名>/<需求名>/specs/` 下的最新文件
- `plan` → `docs/cs/<项目标识符>/<迭代名>/<需求名>/plans/` 下的最新文件
- `api` → `docs/cs/<项目标识符>/<迭代名>/<需求名>/api/` 下的最新文件
- `other` → 询问用户指定文件路径

如果不确定路径，列出 `docs/cs/` 下的目录结构让用户确认。

询问用户：
- 选项 A：读取指定路径的文件（默认路径已提示）
- 选项 B：手动粘贴内容

### 第 4 步：上传

文档类型与 `document_type` 映射：
- `design` / `设计文档` → `"design"`
- `plan` / `计划文档` → `"analysis"`
- `api` / `API文档` → `"api"`
- `other` / `其他` → `"other"`

调用：
```
create_document(
  requirement_id = <需求 ID>,
  title = <文档标题，从文件名或内容首行提取>,
  content = <文档完整 Markdown 内容>,
  document_type = <对应类型>
)
```

### 第 5 步：告知结果

```
✅ 文档已上传
   类型：<文档类型>
   标题：<文档标题>
   关联需求：<需求标题>
```
