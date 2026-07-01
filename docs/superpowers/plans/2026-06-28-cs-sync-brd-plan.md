# /cs_sync_brd 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `/cs_sync_brd` 斜杠命令，让 AI agent 能将本地需求产出（文档、任务、测试记录、状态）一键补推到 CodeSeer 平台。

**Architecture:** 三步交付——①写命令文件本体；②后端 `_setup_dev_environment` 增加分发该文件；③`cs_setup.md` 安装/删除列表同步更新。无新增 API，复用现有 MCP 工具。

**Tech Stack:** Markdown 命令文件、Python（FastAPI MCP handler）

## Global Constraints

- 命令文件格式与 `cs_doc.md`、`cs_start.md` 保持一致（YAML frontmatter + Markdown 正文）
- MCP 工具名称使用已有工具：`list_my_requirements`、`create_document`、`sync_tasks`、`submit_test_result`、`update_requirement_status`
- 本地文档路径约定：`docs/cs/<project_name>/<iteration_name>/<requirement_name>/`
- 单步失败不中断整体流程，在汇总报告中标记 ❌
- 唯一中断条件：本地目录不存在

---

### Task 1: 创建 cs_sync_brd.md 命令文件

**Files:**
- Create: `aicode/commands/cs_sync_brd.md`

**Interfaces:**
- Produces: `/cs_sync_brd` 斜杠命令，供 Task 2 和 Task 3 引用文件路径

- [ ] **Step 1: 创建命令文件**

写入 `aicode/commands/cs_sync_brd.md`，完整内容如下：

```markdown
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
```

- [ ] **Step 2: 验证文件存在且格式正确**

```bash
head -5 aicode/commands/cs_sync_brd.md
```

期望输出包含 `---` frontmatter 和 `description:` 字段。

- [ ] **Step 3: Commit**

```bash
git add aicode/commands/cs_sync_brd.md
git commit -m "feat: add /cs_sync_brd command file"
```

---

### Task 2: 后端 mcp_handlers.py 增加 cs_sync_brd 分发

**Files:**
- Modify: `backend/app/api/mcp_handlers.py`（`_setup_dev_environment` 函数，约第 556–599 行）

**Interfaces:**
- Consumes: `aicode/commands/cs_sync_brd.md`（Task 1 产出）
- Produces: `_setup_dev_environment` 返回值中包含 cs_sync_brd 内容，供 cs_setup 安装

- [ ] **Step 1: 在 _setup_dev_environment 中读取 cs_sync_brd**

在 `mcp_handlers.py` 第 561 行（`cs_skill_content = _read_cmd("cs_skill")`）之后添加：

```python
    cs_sync_brd_content = _read_cmd("cs_sync_brd")
```

- [ ] **Step 2: 在安装指南 sections 中加入 cs_sync_brd 安装行**

找到第 584–586 行的安装指令块：

```python
            f"将【cs_start 命令文件】写入 `$PROJECT_ROOT/{cmd_dir}/cs_start.md`\n"
            f"将【cs_doc 命令文件】写入 `$PROJECT_ROOT/{cmd_dir}/cs_doc.md`\n"
            f"将【cs_skill 命令文件】写入 `$PROJECT_ROOT/{cmd_dir}/cs_skill.md`\n"
```

在 `cs_skill` 行之后追加：

```python
            f"将【cs_sync_brd 命令文件】写入 `$PROJECT_ROOT/{cmd_dir}/cs_sync_brd.md`\n"
```

- [ ] **Step 3: 在 return 的 content 列表中追加 cs_sync_brd 内容块**

找到第 597 行：

```python
            {"type": "text", "text": f"【cs_skill 命令文件】\n\n{cs_skill_content}"},
```

在其后追加：

```python
            {"type": "text", "text": f"【cs_sync_brd 命令文件】\n\n{cs_sync_brd_content}"},
```

- [ ] **Step 4: 验证 Python 语法无误**

```bash
cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend
python -c "import app.api.mcp_handlers; print('OK')"
```

期望输出：`OK`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/mcp_handlers.py
git commit -m "feat: serve cs_sync_brd via setup_dev_environment"
```

---

### Task 3: 更新 cs_setup.md 的删除和安装列表

**Files:**
- Modify: `aicode/commands/cs_setup.md`

**Interfaces:**
- Consumes: Task 1 产出的文件路径 `cs_sync_brd.md`

- [ ] **Step 1: 在删除列表中加入 cs_sync_brd（Claude Code 部分）**

找到（第 51 行）：
```
- `<PROJECT_ROOT>/.claude/commands/cs_skill.md`
```

在其后添加：
```
- `<PROJECT_ROOT>/.claude/commands/cs_sync_brd.md`
```

- [ ] **Step 2: 在删除列表中加入 cs_sync_brd（OpenCode 部分）**

找到（第 60 行）：
```
- `<PROJECT_ROOT>/.opencode/commands/cs_skill.md`
```

在其后添加：
```
- `<PROJECT_ROOT>/.opencode/commands/cs_sync_brd.md`
```

- [ ] **Step 3: 在安装列表中加入 cs_sync_brd（Claude Code 部分）**

找到（第 71 行）：
```
- 【cs_skill 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_skill.md`
```

在其后添加：
```
- 【cs_sync_brd 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_sync_brd.md`
```

- [ ] **Step 4: 在安装列表中加入 cs_sync_brd（OpenCode 部分）**

找到（第 78 行）：
```
- 【cs_skill 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_skill.md`
```

在其后添加：
```
- 【cs_sync_brd 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_sync_brd.md`
```

- [ ] **Step 5: 更新安装结果示例输出**

找到（第 93 行）：
```
/cs_skill 命令         ✅ .opencode/commands/cs_skill.md
```

在其后添加：
```
/cs_sync_brd 命令      ✅ .opencode/commands/cs_sync_brd.md
```

- [ ] **Step 6: 验证四处修改均已写入**

```bash
grep "cs_sync_brd" aicode/commands/cs_setup.md
```

期望输出：4 行（删除×2 + 安装×2）加上示例行，共 5 行。

- [ ] **Step 7: Commit**

```bash
git add aicode/commands/cs_setup.md
git commit -m "feat: add cs_sync_brd to cs_setup install/uninstall lists"
```
