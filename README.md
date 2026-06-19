# CodeSeer

> 让 AI 既懂需求，也懂代码——从需求分配到自动开发的完整闭环

CodeSeer 是一套面向研发团队的 AI 辅助研发平台。产品经理在平台上管理需求，开发者在 Claude Code / OpenCode / Cursor 等 AI 编码工具中直接拉取需求、自动完成开发全流程。

---

## 适合谁用

| 角色 | 主要使用场景 |
|------|-------------|
| **产品经理** | 创建需求、描述验收标准、追踪开发进度 |
| **项目经理** | 创建迭代、分配需求给开发者、查看早会视图 |
| **开发者** | 通过 AI 工具认领需求、头脑风暴、TDD 开发、提交测试结果 |
| **管理员** | 管理用户账号、配置状态机和自定义字段 |

---

## 产品经理 / 项目经理使用流程

### 1. 创建项目和迭代

登录后进入**项目**页面，新建项目，再在项目下创建迭代（Sprint）。

### 2. 添加需求

在迭代下添加需求，填写：
- **标题**：一句话描述功能
- **描述**：详细说明背景和目标
- **验收标准**：明确可测试的完成条件
- **优先级 / 截止日期**

### 3. 分配给开发者

需求分析完成后，将状态推进到 `assigned`，指定负责的开发者。开发者会在 AI 工具中看到该需求。

### 4. 追踪进度

- **早会视图**：按开发者聚合进度，延期需求自动标红
- **需求详情**：查看任务拆解、TDD 进度、测试结果
- **活动日志**：全字段变更时间线

---

## 开发者使用流程

### 第 1 步：接入 AI 工具

在你的 AI 编码工具中配置 CodeSeer MCP：

**Claude Code**（项目根目录 `.mcp.json`）：
```json
{
  "mcpServers": {
    "codeseer": {
      "type": "http",
      "url": "http://<服务器地址>:8000/api/mcp/http",
      "headers": { "Authorization": "Bearer <你的 Token>" }
    }
  }
}
```

**OpenCode**（`~/.opencode/opencode.json`）：
```json
{
  "mcp": {
    "codeseer": {
      "type": "remote",
      "url": "http://<服务器地址>:8000/api/mcp/http",
      "headers": { "Authorization": "Bearer <你的 Token>" }
    }
  }
}
```

> Token 在 CodeSeer Web 界面 → 个人设置 → Access Token 中申请。

### 第 2 步：安装开发环境

AI 工具连上 CodeSeer 后会**自动**将 `/setup_cs_env` 命令安装到当前项目目录。

在 AI 工具中执行：
```
/setup_cs_env
```

这会自动完成：
1. 检查并安装 [Superpowers](https://github.com/obra/superpowers) 技能包
2. 安装 CodeSeer 专属工作流技能到项目目录

### 第 3 步：开始开发

在 AI 工具中说：
```
我要开始工作
```
或输入 `/start-dev`，AI 会引导你完成：

```
选项目 → 选迭代 → 选需求
        ↓
  需求澄清（边界确认、验收标准拆解）
        ↓
  任务拆分（同步到 CodeSeer 平台）
        ↓
  TDD 开发（Red → Green → Refactor）
        ↓
  提交测试结果 → 推进需求到待评审
```

---

## 需求状态说明

| 状态 | 说明 |
|------|------|
| `draft` | 草稿，产品填写中 |
| `pending_analysis` | 待分析 |
| `analyzed` | 已分析，可分配 |
| `assigned` | 已分配给开发者 |
| `claimed` | 开发者已认领 |
| `in_progress` | 开发中 |
| `pending_review` | 待代码评审 |
| `review_approved` | 评审通过 |
| `completed` | 已完成 |

---

## 快速部署

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm install && npm run dev
```

访问 `http://localhost:5173`，默认管理员账号：`admin` / `admin`

> 技术架构、API 文档、MCP 工具详情见 [docs/technical.md](docs/technical.md)

---

## 许可证

MIT
