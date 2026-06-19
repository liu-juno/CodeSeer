---
description: 启动 CodeSeer AI 开发工作流（选项目 → 选迭代 → 选需求 → 头脑风暴）
---

按以下步骤执行 CodeSeer 开发工作流：

1. 调用 `list_my_projects` 获取项目列表，展示给用户选择
2. 用户选择项目后，调用 `list_iterations(project_id)` 展示迭代列表
3. 用户选择迭代后，调用 `list_my_requirements(iteration_id)` 展示分配给当前开发者的需求
4. 用户选择需求后，调用 `start_brainstorming(requirement_id)` 锁定需求并加载完整上下文
5. 基于返回的上下文引导用户进行需求澄清：
   - 需求的功能边界是什么？哪些场景不在范围内？
   - 验收标准中每一项是否可观测/可测试？
   - 是否存在跨模块依赖或与现有 API 的冲突？

如果用户已知道 requirement_id，可跳过前三步直接调用 `start_brainstorming`。