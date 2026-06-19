---
name: codeseer-integration
description: "You MUST use this when the user wants to start development work via CodeSeer platform — triggers the full workflow: select project → select iteration → select requirement → start brainstorming"
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

### 第 7 步：锁定需求，开始头脑风暴
调用 `start_brainstorming(requirement_id)`，获取需求完整上下文（标题、描述、验收标准、现有任务、测试记录）。

拿到上下文后，引导用户进行需求澄清：
- 需求的功能边界是什么？哪些场景不在范围内？
- 验收标准中每一项是否可观测/可测试？
- 是否存在跨模块依赖或与现有 API 的冲突？

## 注意事项
- 每次只锁定一个需求，第二次调用 `start_brainstorming` 会覆盖之前锁定的需求
- 如果用户已经知道 requirement_id，可以跳过前几步直接调用 `start_brainstorming`
- 完成头脑风暴后，使用 `sync_tasks` 将拆解好的任务同步到平台
