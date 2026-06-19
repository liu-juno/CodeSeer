---
description: 安装或更新 CodeSeer 开发环境（删除旧版本，从服务器拉取最新技能和命令）
---

## 触发条件

用户输入 `/cs_setup` 或说以下任意内容时执行本命令：
- "初始化 CodeSeer"
- "安装 CodeSeer 环境"
- "帮我配置 CodeSeer"
- "更新 CodeSeer 命令"
- "cs 初始化"
- "cs setup"

## 执行步骤

### 第 1 步：检查并安装 superpowers

根据当前 AI 工具类型（Claude Code / OpenCode / Cursor）：
- 检查 superpowers 是否已安装
- 已安装：跳过，输出"superpowers 已安装，跳过"
- 未安装：按指南执行安装命令

### 第 2 步：调用 setup_dev_environment 获取最新文件

调用 MCP 工具 `setup_dev_environment`，获取最新的技能和命令文件内容。

### 第 3 步：删除旧版本文件

在**当前工作目录（cwd）**下，删除以下旧文件（不存在则跳过）：

**Claude Code：**
- `<cwd>/.claude/skills/codeseer-integration/` 整个目录
- `<cwd>/.claude/skills/cs_integration/SKILL.md`
- `<cwd>/.claude/commands/setup_cs_env.md`
- `<cwd>/.claude/commands/start_cs.md`
- `<cwd>/.claude/commands/upload_doc.md`
- `<cwd>/.claude/commands/cs_setup.md`
- `<cwd>/.claude/commands/cs_start.md`
- `<cwd>/.claude/commands/cs_doc.md`

**OpenCode：**
- `<cwd>/.opencode/skills/codeseer-integration/` 整个目录
- `<cwd>/.opencode/skills/cs_integration/SKILL.md`
- `<cwd>/.opencode/commands/setup_cs_env.md`
- `<cwd>/.opencode/commands/start_cs.md`
- `<cwd>/.opencode/commands/upload_doc.md`
- `<cwd>/.opencode/commands/cs_setup.md`
- `<cwd>/.opencode/commands/cs_start.md`
- `<cwd>/.opencode/commands/cs_doc.md`

### 第 4 步：写入最新文件

将 `setup_dev_environment` 返回的内容写入对应路径（目录不存在时先创建）：

**Claude Code：**
- 【cs_integration 技能文件】→ `<cwd>/.claude/skills/cs_integration/SKILL.md`
- 【cs_setup 命令文件】→ `<cwd>/.claude/commands/cs_setup.md`
- 【cs_start 命令文件】→ `<cwd>/.claude/commands/cs_start.md`
- 【cs_doc 命令文件】→ `<cwd>/.claude/commands/cs_doc.md`

**OpenCode：**
- 【cs_integration 技能文件】→ `<cwd>/.opencode/skills/cs_integration/SKILL.md`
- 【cs_setup 命令文件】→ `<cwd>/.opencode/commands/cs_setup.md`
- 【cs_start 命令文件】→ `<cwd>/.opencode/commands/cs_start.md`
- 【cs_doc 命令文件】→ `<cwd>/.opencode/commands/cs_doc.md`

### 第 5 步：输出安装结果

告知用户：
- ✅ cs_integration 技能已更新
- ✅ /cs_setup 命令已更新
- ✅ /cs_start 命令已更新
- ✅ /cs_doc 命令已更新
- 现在可以说"我要开始工作"或输入 /cs_start 启动开发工作流
