---
description: 拉取 CodeSeer 项目的模块 Skill 并安装到本地 AI 工具
---

## 触发条件

用户输入 `/cs_skill` 或说以下任意内容时执行本命令：
- "拉取模块 Skill" / "安装模块技能"
- "更新 Skill" / "同步 Skill"
- "cs skill" / "cs_skill"

## 执行步骤

### 第 1 步：确定项目根目录

运行以下命令获取 Git 仓库根目录：

```bash
git rev-parse --show-toplevel
```

将输出结果记为 `<PROJECT_ROOT>`。若不在 git 仓库中，使用 `pwd` 的输出。

> ⚠️ **不能使用 `~` 或 `$HOME`**。必须使用绝对路径。

### 第 2 步：让用户选择项目

调用 MCP 工具 `list_member_projects` 获取项目列表，向用户展示：

```
以下是你参与的项目，请选择要安装 Skill 的项目（输入编号或"全部"）：
1. 项目A（id: xxx）
2. 项目B（id: yyy）
```

等待用户回复。

### 第 3 步：拉取 Skill

根据用户选择：

**选择单个项目：**
调用 `list_skills_by_project(project_id="<选中的项目 id>")`

**选择"全部"：**
对每个项目依次调用 `list_skills_by_project(project_id="<project_id>")`

### 第 4 步：安装 Skill 文件

对返回的每个 Skill，将其 `prompt_template` 内容写入本地文件。

**目录名规则：** Skill 名称（空格替换为下划线），例如 `CodeSeer_AI_Agent_领域知识`

**Claude Code：**
```
$PROJECT_ROOT/.claude/skills/<目录名>/SKILL.md
```

**OpenCode：**
```
$PROJECT_ROOT/.opencode/skills/<目录名>/SKILL.md
```

**Cursor：**
```
$PROJECT_ROOT/.cursor/skills/<目录名>/SKILL.md
```

目录不存在时先 `mkdir -p`，文件已存在则覆盖。

### 第 5 步：向用户汇报

安装完成后，输出安装清单：

```
✅ 已安装 X 个模块 Skill：
- CodeSeer_AI_Agent_领域知识 → .claude/skills/CodeSeer_AI_Agent_领域知识/SKILL.md
- CodeSeer_订单系统_业务规范 → .claude/skills/CodeSeer_订单系统_业务规范/SKILL.md
```

> 💡 Skill 已安装到本地，当前会话立即生效。后续 AI 在处理对应模块需求时会自动加载该 Skill。
