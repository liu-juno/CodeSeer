---
description: 安装 CodeSeer 开发环境（superpowers 技能包 + CodeSeer 专属技能）
---

调用 MCP 工具 `setup_dev_environment` 获取安装指南，然后严格按以下步骤执行：

1. 根据当前 AI 工具类型（Claude Code / OpenCode / Cursor），找到对应的 superpowers 检查路径
2. 检查 superpowers 是否已安装：
   - 已安装：跳过安装，输出"superpowers 已安装，跳过"
   - 未安装：按指南执行安装命令
3. 将工具返回的 codeseer-integration 技能内容写入对应路径（目录不存在时先创建）
4. 输出安装结果摘要