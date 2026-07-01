---
description: 将本地需求产出（文档、任务、测试记录）批量补推到 CodeSeer 平台。用法：/cs_sync_brd [requirement_id]
---

## 参数说明

- 无参数：展示需求列表，用户选择
- 传入 `requirement_id`：跳过选择步骤，直接同步指定需求

## 执行步骤

### 第 1 步：选择需求

**如果传入了 requirement_id 参数**，跳到第 2 步。

**否则**，调用 `list_my_requirements` 展示需求列表：

```
以下是指派给你的需求，请选择要补推的需求（输入编号）：
1. <需求名> [<状态>] — 迭代：<迭代名>
2. ...
```

等待用户选择，记录：
- `requirement_id`
- `project_name`（项目标识符，如 "codeseer"）
- `iteration_name`（迭代名，如 "sprint-1"）
- `requirement_name`（需求名，如 "创建需求支持上传附件"）

### 第 2 步：确定本地路径并扫描产出

构建本地路径：
```
local_path = docs/cs/<project_name>/<iteration_name>/<requirement_name>/
```

检查以下目录是否存在且含 `.md` 文件：
- `<local_path>/specs/`
- `<local_path>/plans/`

**两个目录均不存在或为空时**，报错退出：
```
❌ 未找到本地产出目录：<local_path>
   请确认文件是否保存在正确路径，或使用 /cs_doc 手动上传单个文件。
```

**否则**，列出找到的文件并等待确认：
```
📁 找到以下本地产出，即将推送到需求「<requirement_name>」：

设计文档（specs/）：
  - <文件名>.md

计划文档（plans/）：
  - <文件名>.md

继续？(Y/n)
```

### 第 3 步：推送设计文档

遍历 `<local_path>/specs/` 下所有 `.md` 文件，逐个调用：

```
create_document(
  requirement_id = <requirement_id>,
  title          = <从文件首行 # 标题提取，若无则用文件名去掉 .md>,
  content        = <文件完整内容>,
  document_type  = "design"
)
```

每个文件输出进度：`  ✅ 设计文档：<文件名>` 或 `  ❌ <文件名>：<错误原因>`。

### 第 4 步：推送计划文档

遍历 `<local_path>/plans/` 下所有 `.md` 文件，逐个调用：

```
create_document(
  requirement_id = <requirement_id>,
  title          = <从文件首行 # 标题提取，若无则用文件名去掉 .md>,
  content        = <文件完整内容>,
  document_type  = "analysis"
)
```

每个文件输出进度：`  ✅ 计划文档：<文件名>` 或 `  ❌ <文件名>：<错误原因>`。

### 第 5 步：同步任务列表

读取 `<local_path>/plans/` 下所有文件，提取符合以下格式的任务标题：

```
### Task N: <任务标题>
```

将标题后到下一个 `### Task` 或文件末尾之间的内容作为描述。

调用：
```
sync_tasks(
  requirement_id = <requirement_id>,
  tasks = [
    {"title": "<任务标题>", "description": "<描述段落，若无则省略>"},
    ...
  ]
)
```

- 未提取到任务时：输出 `⚠️ 未在计划文档中找到 Task，跳过任务同步` 并继续
- 成功时：记录返回的任务 ID 列表 `task_ids`

### 第 6 步：同步测试记录

检查 `.superpowers/sdd/progress.md` 是否存在。

**存在时**：解析文件中每个任务的 TDD 阶段结果，对每条记录调用：
```
submit_test_result(
  requirement_id = <requirement_id>,
  task_id        = <按任务标题从 task_ids 匹配的 id>,
  tdd_phase      = "red" | "green" | "refactor",
  total_count    = <总用例数>,
  passed_count   = <通过数>,
  failed_count   = <失败数>
)
```

**不存在时**：询问用户：
```
未找到 TDD 测试记录（.superpowers/sdd/progress.md 不存在）。

A. 现在运行测试 — 请运行测试命令后将结果粘贴给我
B. 跳过测试记录同步
```

- 选 A：等待用户粘贴测试输出，解析后为所有已同步任务提交 `tdd_phase="green"` 记录
- 选 B：跳过，汇总标记 `⚠️ 测试记录未同步`

### 第 7 步：推进需求状态

询问用户：
```
是否将需求「<requirement_name>」状态推进为「待评审」？(Y/n)
```

确认后调用：
```
update_requirement_status(requirement_id=<requirement_id>, action="pending_review")
```

拒绝则跳过，汇总标记 `⏭️ 状态未变更`。

### 第 8 步：汇总报告

```
✅ /cs_sync_brd 推送完成
━━━━━━━━━━━━━━━━━━━━━━━━━━
需求：<requirement_name>

✅ 设计文档：N 份已上传
✅ 计划文档：N 份已上传
✅ 任务：N 条已同步
✅ 测试记录：N 条已提交     ← 或 ⚠️ 测试记录未同步
✅ 需求状态：已推进为「待评审」  ← 或 ⏭️ 状态未变更

❌ 失败项（若有）：
  - <文件名>：<错误原因>
```
