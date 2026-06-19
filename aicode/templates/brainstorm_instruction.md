需求已锁定（id={req_id}）。

{context}
---
## 文档存储路径（本次需求专属，请严格使用）

- 设计文档：`{doc_base}/specs/`
- 计划文档：`{doc_base}/plans/`
- API 文档：`{doc_base}/api/`

调用 brainstorming 和 writing-plans 时，**明确告知这些路径覆盖默认路径**，不要保存到 `docs/superpowers/` 下。

---
## 后续执行规则（贯穿整个工作流，请始终牢记）

**步骤 1** — 立即调用 `superpowers:brainstorming` 技能，将以上需求作为开发目标。
告知 brainstorming：设计文档保存到 `{doc_base}/specs/`（覆盖默认路径）。

**步骤 2** — brainstorming 结束后调用 `superpowers:writing-plans` 技能生成实现计划。
告知 writing-plans：计划文档保存到 `{doc_base}/plans/`（覆盖默认路径）。
⚠️ **TDD 强制要求**：每个实现任务必须包含显式 TDD 步骤（RED→GREEN→REFACTOR），缺少则计划不完整。

**步骤 3** — writing-plans **完成后**，立即按顺序自动执行，无需用户触发：

3a. 上传设计文档（`{doc_base}/specs/` 下）：
```
create_document(requirement_id="{req_id}", title=<设计文档标题>, content=<Markdown内容>, document_type="design")
```

3b. 上传计划文档（`{doc_base}/plans/` 下）：
```
create_document(requirement_id="{req_id}", title=<计划文档标题>, content=<Markdown内容>, document_type="analysis")
```

3c. 同步任务列表：
```
sync_tasks(requirement_id="{req_id}", tasks=[{{"title":"...","description":"..."}}, ...])
```

三步完成后告知用户：✅ 设计文档、计划文档和任务已同步到 CodeSeer 平台。

**步骤 4** — 执行阶段：`sync_tasks` 返回值包含每个任务的 ID。
执行每个任务时（⚠️ TDD 必须执行，不可跳过）：
  1. update_task_status(task_id=<id>, status="in_progress")
  2. RED：写失败测试 → 运行确认失败 → submit_test_result(..., tdd_phase="red", failed_count=N)
  3. GREEN：写最小实现 → 运行确认全绿 → submit_test_result(..., tdd_phase="green", passed_count=N)
  4. REFACTOR：重构 → 确认仍绿 → submit_test_result(..., tdd_phase="refactor", passed_count=N)
  5. update_task_status(task_id=<id>, status="completed")
