已连接 CodeSeer 平台。

## 重要：两类触发，不要混淆

### 触发一：环境安装

用户说以下任意内容时，执行环境安装（不是开发流程）：
- 初始化 CodeSeer / 初始化cs / 初始化 cs
- 安装 CodeSeer 环境
- 帮我配置 CodeSeer
- 更新 CodeSeer 命令
- cs 初始化 / cs setup

安装动作：
1. 调用 setup_dev_environment 工具
2. 删除旧文件（codeseer-integration目录、setup_cs_env.md、start_cs.md、upload_doc.md）
3. 写入新文件到 cwd（不是用户主目录）：
   Claude Code: <cwd>/.claude/skills/cs_integration/SKILL.md
               <cwd>/.claude/commands/{cs_setup,cs_start,cs_doc}.md
   OpenCode:   <cwd>/.opencode/skills/cs_integration/SKILL.md
               <cwd>/.opencode/commands/{cs_setup,cs_start,cs_doc}.md
4. 告知用户安装完成，可用 /cs_start 开始工作

### 触发二：开发工作流

用户说「我要开始工作」「开始开发」等开发意图时，执行 cs_start 工作流（选项目→选需求→头脑风暴）。
