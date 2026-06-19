---
description: 启动 CodeSeer AI 开发工作流（TDD 强制 · 自动同步文档和任务状态）
---

> ⚠️ **TDD 强制规则**：本工作流所有实现任务必须使用 TDD。没有 RED→GREEN→REFACTOR 步骤的任务不得进入实现阶段。

## 工作流步骤

1. 调用 `list_my_projects` 获取项目列表，展示给用户选择
2. 用户选择项目后，调用 `list_iterations(project_id)` 展示迭代列表
3. 用户选择迭代后，调用 `list_my_requirements(iteration_id)` 展示分配给当前开发者的需求
4. 用户选择需求后，调用 `start_brainstorming(requirement_id)` 锁定需求
5. 收到返回后，立即调用 `superpowers:brainstorming` 技能
6. brainstorming 完成后，调用 `superpowers:writing-plans` 生成实现计划

   **⚠️ 检查**：计划中每个实现任务必须包含显式 TDD 步骤（RED/GREEN/REFACTOR）。若缺少，补充后再继续。

---

### writing-plans 完成后自动执行（不等用户触发，按顺序）

**A — 上传设计文档**（`docs/cs/<迭代名>/<需求名>/specs/`，brainstorming 产出）
```
create_document(requirement_id, title, content, document_type="design")
```

**B — 上传计划文档**（`docs/cs/<迭代名>/<需求名>/plans/`，writing-plans 产出）
```
create_document(requirement_id, title, content, document_type="analysis")
```

**C — 同步任务列表**（从计划提取所有 Task，返回值含任务 ID）
```
sync_tasks(requirement_id, tasks=[{"title":"...", "description":"..."}, ...])
```

完成后告知用户：**✅ 设计文档、计划文档和任务已同步到 CodeSeer 平台**

---

### 执行阶段：每个任务（TDD 强制 · 状态实时更新）

`sync_tasks` 返回值包含每个任务的 ID，执行时：

1. `update_task_status(task_id, "in_progress")` — 开始前标记
2. 调用 `superpowers:test-driven-development` 技能，严格按以下节奏：

   **RED** — 写失败测试 → 运行确认失败 → 上报：
   ```
   submit_test_result(requirement_id, task_id, tdd_phase="red",
                      total_count=N, passed_count=0, failed_count=N,
                      failed_tests="失败用例名...")
   ```

   **GREEN** — 写最小实现 → 运行确认全部通过 → 上报：
   ```
   submit_test_result(requirement_id, task_id, tdd_phase="green",
                      total_count=N, passed_count=N, failed_count=0,
                      coverage=<覆盖率>)
   ```

   **REFACTOR** — 重构 → 确认仍全绿 → 上报：
   ```
   submit_test_result(requirement_id, task_id, tdd_phase="refactor",
                      total_count=N, passed_count=N, failed_count=0)
   ```

3. `update_task_status(task_id, "completed")` — 完成后标记
4. 进入下一个任务

---

> 如果用户已知道 requirement_id，可跳过步骤 1-3 直接调用 `start_brainstorming`。
