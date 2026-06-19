---
description: 启动 CodeSeer AI 开发工作流（选项目 → 选迭代 → 选需求 → 头脑风暴 → 自动同步文档和任务）
---

按以下步骤执行 CodeSeer 开发工作流：

1. 调用 `list_my_projects` 获取项目列表，展示给用户选择
2. 用户选择项目后，调用 `list_iterations(project_id)` 展示迭代列表
3. 用户选择迭代后，调用 `list_my_requirements(iteration_id)` 展示分配给当前开发者的需求
4. 用户选择需求后，调用 `start_brainstorming(requirement_id)` 锁定需求
5. 收到返回后，立即调用 `superpowers:brainstorming` 技能
6. brainstorming 完成后，`superpowers:writing-plans` 生成实现计划

---

### writing-plans 完成后自动执行（不等用户触发，按顺序）

**Step A — 上传设计文档**（`docs/superpowers/specs/` 下，brainstorming 产出）
```
create_document(requirement_id, title, content, document_type="design")
```

**Step B — 上传计划文档**（`docs/superpowers/plans/` 下，writing-plans 产出）
```
create_document(requirement_id, title, content, document_type="analysis")
```

**Step C — 同步任务列表**（从计划文档提取所有 Task）
```
sync_tasks(requirement_id, tasks=[{"title":"...", "description":"..."}, ...])
```

三步完成后告知用户：**✅ 设计文档、计划文档和任务已同步到 CodeSeer 平台**

---

7. 用户选择执行方式（Subagent-Driven / Inline Execution），按 TDD 节奏实现每个任务

**Step D — 执行阶段实时更新任务状态**（`sync_tasks` 返回值中含各任务 ID）

每个任务执行时：
- 开始前：`update_task_status(task_id=<id>, status="in_progress")`
- 完成后：`update_task_status(task_id=<id>, status="completed")`

> 如果用户已知道 requirement_id，可跳过步骤 1-3 直接调用 `start_brainstorming`。
