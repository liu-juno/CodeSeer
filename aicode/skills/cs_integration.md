---
name: cs_integration
description: "Use ONLY when user explicitly says they want to START DEVELOPMENT WORK (e.g. '我要开始工作', '开始开发', '/cs_start'). Do NOT use for setup/initialization phrases like '初始化', 'cs setup', '安装环境', '配置' — those belong to cs_setup."
---

# CodeSeer Integration Skill

## TDD 强制规则

> ⚠️ **本技能的所有开发任务强制使用 TDD（测试驱动开发）。**
> 没有 TDD 步骤的任务不允许进入实现阶段。跳过 TDD 不是"提效"，是引入无法追踪的风险。

## 触发条件

用户输入 `/cs_start` 或表达以下**开发**意图时触发（注意：安装/初始化不属于此范围）：
- "我要开始工作"
- "开始开发"
- "我有新任务"
- "开始一个新需求"
- "start dev"

## ⛔ 不触发条件（交给环境安装流程处理）

以下内容**不属于开发工作流**，不要用本技能处理：
- "初始化" / "初始化cs" / "初始化 cs" / "初始化 CodeSeer"
- "cs 初始化" / "cs setup"
- "安装 CodeSeer 环境" / "帮我配置 CodeSeer" / "更新 CodeSeer 命令"

遇到上述触发词，应调用 `setup_dev_environment` 工具执行安装流程，而不是开发流程。

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
调用 `list_my_requirements(iteration_id)`，展示指派给当前开发者的需求。

### 第 6 步：开发者选择需求
等待用户选择需求，记录 `requirement_id`。

### 第 7 步：锁定需求，启动头脑风暴
调用 `start_brainstorming(requirement_id)`，获取需求完整上下文。

收到返回后，**立即调用 `superpowers:brainstorming` 技能**（Skill 工具，`skill='superpowers:brainstorming'`）。

### 第 8 步：writing-plans（必须包含 TDD 步骤）

brainstorming 完成后调用 `superpowers:writing-plans`。

**⚠️ 检查点**：writing-plans 生成的计划文件中，每一个实现任务必须包含以下 TDD 子步骤，否则计划不完整，需补充后才能继续：

```
1. 写失败测试（RED）—— 描述测试用例的期望行为
2. 运行测试，确认失败（验证测试有效性）
3. 写最小实现代码（GREEN）—— 只写够让测试通过的代码
4. 运行测试，确认全部通过
5. 重构（REFACTOR）—— 在保持绿灯的前提下改善代码质量
6. 提交
```

### 第 9 步：writing-plans 完成后自动同步（无需用户触发）

writing-plans 将计划写入 `start_brainstorming` 返回的路径（`docs/cs/<迭代名>/<需求名>/plans/`）后，**立即按顺序执行**：

**9a. 上传设计文档**（`docs/cs/<迭代名>/<需求名>/specs/` 下，brainstorming 产出）
```
create_document(requirement_id, title, content, document_type="design")
```

**9b. 上传计划文档**（`docs/cs/<迭代名>/<需求名>/plans/` 下，writing-plans 产出）
```
create_document(requirement_id, title, content, document_type="analysis")
```

**9c. 同步任务列表**（从计划文档提取所有 Task）
```
sync_tasks(requirement_id, tasks=[{"title": "...", "description": "..."}, ...])
```

同步成功后告知用户：**✅ 设计文档、计划文档和任务已同步到 CodeSeer 平台**

### 第 10 步：执行阶段（TDD 强制，逐任务更新状态）

用户选择执行方式后，`sync_tasks` 返回值中包含每个任务的 `id`。

**每个任务的执行流程**（不可跳过任何步骤）：

1. `update_task_status(task_id=<id>, status="in_progress")` — 标记开始
2. 调用 `superpowers:test-driven-development` 技能执行该任务，严格按 RED → GREEN → REFACTOR：
   - **RED**：写失败测试 → 运行 → 确认失败后，上报：
     ```
     submit_test_result(requirement_id, task_id, tdd_phase="red",
                        total_count=N, passed_count=0, failed_count=N,
                        failed_tests="失败用例名称...")
     ```
   - **GREEN**：写最小实现 → 运行 → 确认全部通过后，上报：
     ```
     submit_test_result(requirement_id, task_id, tdd_phase="green",
                        total_count=N, passed_count=N, failed_count=0,
                        coverage=<覆盖率百分比>)
     ```
   - **REFACTOR**：重构 → 运行确认仍全绿 → 上报：
     ```
     submit_test_result(requirement_id, task_id, tdd_phase="refactor",
                        total_count=N, passed_count=N, failed_count=0)
     ```
3. `update_task_status(task_id=<id>, status="completed")` — 标记完成
4. 进入下一个任务

## 注意事项
- 第 9、10 步是**自动**执行的，不要等用户说"同步"或"更新状态"
- TDD 是**强制**的，不是可选的。用户说"先跳过测试"也不行
- `sync_tasks` 返回的任务 ID 列表必须保存，执行阶段用于调用 `update_task_status`
- 每次只锁定一个需求；如果用户已知道 requirement_id 可跳过第 1-5 步
