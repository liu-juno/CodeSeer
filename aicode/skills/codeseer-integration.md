---
name: codeseer-integration
description: "You MUST use this when the user wants to start development work via CodeSeer platform — triggers the full workflow: select project → select iteration → select requirement → brainstorming → writing-plans → auto-sync docs & tasks"
---

# CodeSeer Integration Skill

## 触发条件
用户输入 `/start-dev` 或表达以下开发意图时触发：
- "我要开始工作"
- "开始开发"
- "我有新任务"
- "开始一个新需求"
- "start dev"

## 执行流程

### 第 1 步：获取项目列表
调用 MCP 工具 `list_my_projects`，展示当前开发者有未完成需求的项目。

### 第 2 步：开发者选择项目
将项目列表展示给用户，等待用户选择，记录 `project_id`。

### 第 3 步：获取迭代列表
调用 `list_iterations(project_id)`，展示该项目下的迭代。

### 第 4 步：开发者选择迭代
等待用户选择迭代，记录 `iteration_id`。

### 第 5 步：获取需求列表
调用 `list_my_requirements(iteration_id)`，展示指派给当前开发者的需求（状态为 assigned/claimed/in_progress）。

### 第 6 步：开发者选择需求
等待用户选择需求，记录 `requirement_id`。

### 第 7 步：锁定需求，启动头脑风暴
调用 `start_brainstorming(requirement_id)`，获取需求完整上下文。

收到返回后，**立即调用 `superpowers:brainstorming` 技能**（Skill 工具，`skill='superpowers:brainstorming'`）。

brainstorming 结束后，`superpowers:writing-plans` 技能生成实现计划。

### 第 8 步：writing-plans 完成后自动同步（无需用户触发）

writing-plans 将计划写入 `docs/superpowers/plans/` 后，**立即按顺序执行以下三步**：

**8a. 上传设计文档**（brainstorming 阶段产出，在 `docs/superpowers/specs/` 下）
```
create_document(
  requirement_id = <锁定的 requirement_id>,
  title = "<设计文档标题>",
  content = "<完整 Markdown 内容>",
  document_type = "design"
)
```

**8b. 上传计划文档**（writing-plans 阶段产出，在 `docs/superpowers/plans/` 下）
```
create_document(
  requirement_id = <锁定的 requirement_id>,
  title = "<计划文档标题>",
  content = "<完整 Markdown 内容>",
  document_type = "analysis"
)
```

**8c. 同步任务列表**（从计划文档中提取所有 Task）
```
sync_tasks(
  requirement_id = <锁定的 requirement_id>,
  tasks = [{"title": "...", "description": "..."}, ...]
)
```

三步完成后告知用户：**✅ 设计文档、计划文档和任务已同步到 CodeSeer 平台**

### 第 9 步：执行阶段实时更新任务状态

用户选择执行方式后，`sync_tasks` 的返回值中包含每个任务的 `id`。**执行每个任务时**：

- **开始前**：调用 `update_task_status(task_id=<id>, status="in_progress")`
- **完成后**：调用 `update_task_status(task_id=<id>, status="completed")`

这样平台上可以实时看到每个任务的开发进度，无需等到全部完成才更新。

## 注意事项
- 第 8、9 步是**自动**执行的，不要等用户说"同步"或"更新状态"才去做
- 设计文档在 `docs/superpowers/specs/` 下，计划文档在 `docs/superpowers/plans/` 下，两份都要上传
- `sync_tasks` 返回的任务列表含 ID，执行阶段用这些 ID 调 `update_task_status`
- 每次只锁定一个需求，如果用户已知道 requirement_id 可跳过前六步直接调用 `start_brainstorming`
