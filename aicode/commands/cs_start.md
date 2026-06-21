---
description: 启动 CodeSeer AI 开发工作流（TDD 强制 · 自动同步文档和任务状态）
---

> ⚠️ **TDD 强制规则**：本工作流所有实现任务必须使用 TDD。没有 RED→GREEN→REFACTOR 步骤的任务不得进入实现阶段。

## 工作流步骤

1. 调用 `list_my_projects` 获取项目列表：
   - 只有 1 个项目：**自动选择，不询问用户**
   - 多个项目：展示列表，等待用户选择

2. 调用 `list_iterations(project_id)` 获取迭代列表：
   - 只有 1 个迭代：**自动选择，不询问用户**
   - 多个迭代：展示列表，等待用户选择

3. 自动选择或用户选择完成后，**先告知用户当前上下文**：
   ```
   📁 项目：<项目名>
   🔁 迭代：<迭代名>
   ```
   然后调用 `list_my_requirements(iteration_id)` 展示分配给当前开发者的需求列表

4. 用户选择需求后，调用 `start_brainstorming(requirement_id)` 锁定需求
5. 收到返回后，立即调用 `superpowers:brainstorming` 技能
6. brainstorming 完成后，调用 `superpowers:writing-plans` 生成实现计划

   **⚠️ 检查**：计划中每个实现任务必须包含显式 TDD 步骤（RED/GREEN/REFACTOR）。若缺少，补充后再继续。

---

### writing-plans 完成后自动执行（不等用户触发，按顺序）

**A — 上传设计文档**（`docs/cs/<项目标识符>/<迭代名>/<需求名>/specs/`，brainstorming 产出）
```
create_document(requirement_id, title, content, document_type="design")
```

**B — 上传计划文档**（`docs/cs/<项目标识符>/<迭代名>/<需求名>/plans/`，writing-plans 产出）
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

### 所有任务完成后：终态同步

全部任务执行完毕后，**按顺序**执行：

**第一步：同步最终工时**
```
sync_tasks(
  requirement_id = <需求 ID>,
  tasks = [
    {"title": "<任务名>", "status": "completed", "actual_hours": <实际工时>},
    ...
  ]
)
```

> 按 title 匹配已有任务进行更新，不会删除已有记录。

**第二步：提交待评审**
```
update_requirement_status(requirement_id=<需求 ID>, action="pending_review")
```

> ⚠️ **必须调用**，否则平台需求状态将停留在"开发中"，PM 无法感知到需求已完成等待评审。

---

> 如果用户已知道 requirement_id，可跳过步骤 1-3 直接调用 `start_brainstorming`。
