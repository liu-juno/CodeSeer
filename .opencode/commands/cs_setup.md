---
description: 安装或更新 CodeSeer 开发环境（删除旧版本，从服务器拉取最新技能和命令）
---

## 触发条件

用户输入 `/cs_setup` 或说以下任意内容时执行本命令：
- "初始化 CodeSeer" / "初始化cs" / "初始化 cs"
- "安装 CodeSeer 环境"
- "帮我配置 CodeSeer"
- "更新 CodeSeer 命令"
- "cs 初始化" / "cs setup"

## 执行步骤

### 第 1 步：检查并安装 superpowers

根据当前 AI 工具类型（Claude Code / OpenCode / Cursor）：
- 检查 superpowers 是否已安装
- 已安装：跳过，输出"superpowers 已安装，跳过"
- 未安装：按指南执行安装命令

### 第 2 步：确定项目根目录

运行以下命令获取 Git 仓库根目录：

```bash
git rev-parse --show-toplevel
```

将输出结果记为 `<PROJECT_ROOT>`。

- 如果成功：使用该路径（例如 `/Users/dev/myproject`）
- 如果失败（不在 git 仓库中）：使用当前工作目录（`pwd` 的输出）

> ⚠️ **不能使用 `~` 或 `$HOME`**。必须使用上述命令获取的绝对路径。

### 第 3 步：调用 setup_dev_environment 获取最新文件

调用 MCP 工具 `setup_dev_environment`，获取最新的技能和命令文件内容。

### 第 4 步：删除旧版本文件

在 `<PROJECT_ROOT>` 下删除旧文件（不存在则跳过）：

**Claude Code：**
- `<PROJECT_ROOT>/.claude/skills/codeseer-integration/` 整个目录
- `<PROJECT_ROOT>/.claude/skills/cs_integration/SKILL.md`
- `<PROJECT_ROOT>/.claude/commands/cs_setup.md`
- `<PROJECT_ROOT>/.claude/commands/cs_start.md`
- `<PROJECT_ROOT>/.claude/commands/cs_doc.md`
- `<PROJECT_ROOT>/.claude/commands/cs_skill.md`
- `<PROJECT_ROOT>/.claude/commands/cs_sync_brd.md`

**OpenCode：**
- `<PROJECT_ROOT>/.opencode/skills/codeseer-integration/` 整个目录
- `<PROJECT_ROOT>/.opencode/skills/cs_integration/SKILL.md`
- `<PROJECT_ROOT>/.opencode/commands/cs_setup.md`
- `<PROJECT_ROOT>/.opencode/commands/cs_start.md`
- `<PROJECT_ROOT>/.opencode/commands/cs_doc.md`
- `<PROJECT_ROOT>/.opencode/commands/cs_skill.md`
- `<PROJECT_ROOT>/.opencode/commands/cs_sync_brd.md`

### 第 5 步：写入最新文件

将 `setup_dev_environment` 返回的内容写入以下路径（目录不存在时先 `mkdir -p` 创建）：

**Claude Code：**
- 【cs_integration 技能】→ `<PROJECT_ROOT>/.claude/skills/cs_integration/SKILL.md`
- 【cs_setup 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_setup.md`
- 【cs_start 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_start.md`
- 【cs_doc 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_doc.md`
- 【cs_skill 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_skill.md`
- 【cs_sync_brd 命令】→ `<PROJECT_ROOT>/.claude/commands/cs_sync_brd.md`

**OpenCode：**
- 【cs_integration 技能】→ `<PROJECT_ROOT>/.opencode/skills/cs_integration/SKILL.md`
- 【cs_setup 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_setup.md`
- 【cs_start 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_start.md`
- 【cs_doc 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_doc.md`
- 【cs_skill 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_skill.md`
- 【cs_sync_brd 命令】→ `<PROJECT_ROOT>/.opencode/commands/cs_sync_brd.md`

### 第 6 步：输出安装结果

告知用户安装路径和结果，例如：

```
安装路径：/Users/dev/myproject/.opencode/

项目                   状态
superpowers            ✅ 已安装
cs_integration 技能    ✅ .opencode/skills/cs_integration/SKILL.md
/cs_setup 命令         ✅ .opencode/commands/cs_setup.md
/cs_start 命令         ✅ .opencode/commands/cs_start.md
/cs_doc 命令           ✅ .opencode/commands/cs_doc.md
/cs_skill 命令         ✅ .opencode/commands/cs_skill.md
/cs_sync_brd 命令      ✅ .opencode/commands/cs_sync_brd.md
```

现在可以说"我要开始工作"或输入 /cs_start 启动开发工作流
安装模块 Skill 请输入 /cs_skill