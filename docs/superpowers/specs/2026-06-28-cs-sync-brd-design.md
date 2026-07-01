# /cs_sync_brd 补推命令设计

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为完成了本地开发但未经 `/cs_start` 自动同步的需求，提供一键补推所有产出到 CodeSeer 平台的命令。

**Architecture:** 一个 Claude Code / OpenCode 斜杠命令文件（`.claude/commands/cs_sync_brd.md`），通过调用已有 MCP 工具完成批量推送，无需新增后端接口。

**Tech Stack:** Markdown 命令文件（与 cs_start.md、cs_doc.md 同格式）、MCP 工具（已有）

---

## 命令定位

| | `/cs_doc` | `/cs_sync_brd` |
|---|---|---|
| 范围 | 单文档手动上传 | 全量批量补推 |
| 交互 | 逐步询问类型/路径/内容 | 只在开头选需求，其余自动执行 |
| 场景 | 精细控制某一份文档 | 补齐整个需求的全部平台数据 |

## 本地路径约定

所有产出必须位于：
```
docs/cs/<project_name>/<iteration_name>/<requirement_name>/
├── specs/   ← brainstorming 设计文档（一或多个 .md 文件）
└── plans/   ← writing-plans 计划文档（一或多个 .md 文件）
```

此路径由 `cs_integration` skill 强制约定。`docs/superpowers/` 不在扫描范围内。

---

## 执行流程

### 第 1 步：选择需求

调用 `list_my_requirements` 展示需求列表，等待用户选择。

若用户直接传入 `requirement_id` 参数（如 `/cs_sync_brd <id>`），跳过此步。

选定后记录：
- `requirement_id`
- `project_name`、`iteration_name`、`requirement_name`（从返回值提取）
- `local_path = docs/cs/<project_name>/<iteration_name>/<requirement_name>/`

### 第 2 步：扫描本地产出

检查 `<local_path>/specs/` 和 `<local_path>/plans/` 是否存在。

- 两个目录均不存在 → 报错退出：
  ```
  ❌ 未找到本地产出目录：<local_path>
  请确认文件是否保存在正确路径，或使用 /cs_doc 手动上传单个文件。
  ```
- 存在则列出找到的文件，告知用户即将推送的内容。

### 第 3 步：推送设计文档

遍历 `specs/` 下所有 `.md` 文件，逐个调用：

```
create_document(
  requirement_id = <requirement_id>,
  title          = <从文件首行 # 标题提取，若无则用文件名>,
  content        = <文件完整内容>,
  document_type  = "design"
)
```

单文件失败记录 ❌ 并继续下一个，不中断整体流程。

### 第 4 步：推送计划文档

遍历 `plans/` 下所有 `.md` 文件，逐个调用：

```
create_document(
  requirement_id = <requirement_id>,
  title          = <从文件首行 # 标题提取，若无则用文件名>,
  content        = <文件完整内容>,
  document_type  = "analysis"
)
```

### 第 5 步：同步任务列表

读取 `plans/` 下所有文件，提取符合以下格式的任务块：

```
### Task N: <任务标题>
```

或计划文档中的 checkbox 列表项（`- [ ] **Step...`）中的父级任务。

调用：
```
sync_tasks(
  requirement_id = <requirement_id>,
  tasks = [
    {"title": "<任务标题>", "description": "<任务描述（若有）>"},
    ...
  ]
)
```

记录返回的 `task_id` 列表供下一步使用。若解析不到任务，跳过此步并提示用户。

### 第 6 步：同步测试记录

检查 `.superpowers/sdd/progress.md` 是否存在并包含 TDD 阶段记录（red/green/refactor）。

**有记录时：** 解析每个任务的 TDD 结果，调用：
```
submit_test_result(
  requirement_id = <requirement_id>,
  task_id        = <对应 task_id>,
  tdd_phase      = "red" | "green" | "refactor",
  total_count    = N,
  passed_count   = N,
  failed_count   = N
)
```

**无记录时：** 询问用户：
```
未找到 TDD 测试记录。
A. 现在运行测试并提交结果
B. 跳过（汇总报告中标记为未同步）
```
- 选 A：提示用户运行项目测试命令，等待结果后调用 `submit_test_result`
- 选 B：跳过，汇总中标记 `⚠️ 测试记录未同步`

### 第 7 步：推进需求状态

询问用户：
```
是否将需求状态推进为「待评审」？(Y/n)
```

确认后调用：
```
update_requirement_status(requirement_id=<requirement_id>, action="pending_review")
```

拒绝则跳过，汇总中标记 `⏭️ 状态未变更`。

### 第 8 步：汇总报告

```
✅ /cs_sync_brd 推送完成

需求：<requirement_name>

✅ 设计文档：N 份已上传
✅ 计划文档：N 份已上传
✅ 任务：N 条已同步
✅ 测试记录：N 条已提交   ← 或 ⚠️ 测试记录未同步
✅ 需求状态：已推进为「待评审」  ← 或 ⏭️ 状态未变更

❌ 失败项（若有）：
- specs/xxx.md 上传失败：<错误原因>
```

---

## 错误处理原则

- **唯一中断条件**：本地目录 `docs/cs/<project>/<iteration>/<requirement>/` 不存在
- **单步失败不中断**：记录 ❌ 后继续执行后续步骤
- **重复上传**：平台允许同一需求多个同类文档，不做去重判断

---

## 命令文件交付位置

与其他命令一致，交付到：
- Claude Code：`aicode/commands/cs_sync_brd.md`（再由 `cs_setup` 分发到 `.claude/commands/`）
- OpenCode：同上分发到 `.opencode/commands/`

`cs_setup.md` 需同步更新，将 `cs_sync_brd.md` 加入安装/删除列表。
