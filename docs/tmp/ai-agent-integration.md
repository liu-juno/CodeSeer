# AI Agent 集成

## 背景

CodeSeer 平台通过 MCP（Model Context Protocol）协议与 AI 编码工具（Claude Code、OpenCode 等）建立双向通信。AI Agent 作为开发者的代理，能够感知平台上的需求上下文、自主推进开发流程，并将执行结果同步回平台。

## 用户故事

作为开发者，我希望 AI 编码工具能直接从平台拉取需求、同步任务进度、上传文档，以便无需在平台和 IDE 之间手动切换，AI 完整代理整个开发流程。

## 架构概述

```
AI 编码工具（Claude Code / OpenCode）
        │
        │  MCP HTTP Transport (JSON-RPC 2.0)
        ▼
CodeSeer MCP Server（/api/mcp/...）
        │
        │  SQLAlchemy Async
        ▼
CodeSeer 业务数据库（SQLite）
```

MCP Server 以独立路由挂载在 FastAPI 主应用下，通过 Bearer Token 鉴权，每个 AI 工具实例对应一个开发者身份。

## MCP 工具清单

### 需求相关

| 工具名 | 说明 |
|--------|------|
| `get_my_requirements` | 拉取指派给当前开发者的待开发需求列表 |
| `get_requirement` | 获取单条需求的完整详情（描述、验收标准、现有任务） |
| `update_requirement_status` | 触发需求状态流转（如 `assigned → in_progress`） |

### 任务相关

| 工具名 | 说明 |
|--------|------|
| `sync_tasks` | 按标题 upsert 任务列表；不删除平台已有任务 |

`sync_tasks` 支持字段：
- `title`：任务标题（匹配键）
- `description`：任务描述
- `status`：`pending` / `in_progress` / `completed` / `blocked`
- `estimated_hours`：预估工时
- `actual_hours`：实际工时

### 测试相关

| 工具名 | 说明 |
|--------|------|
| `submit_test_record` | 上传单元测试执行结果 |

### 文档相关

| 工具名 | 说明 |
|--------|------|
| `create_document` | 上传设计文档（Markdown），关联到指定需求 |

### 环境配置

| 工具名 | 说明 |
|--------|------|
| `setup_dev_environment` | 安装 superpowers 技能包及 CodeSeer 专属 Skill 到本地 AI 工具 |

## 状态流转

简化后的需求状态机：

```
草稿(draft)
  └─ 已指派(assigned)      ← 平台 PM 操作
       └─ 开发中(in_progress)   ← AI 开始开发时调用
            └─ 待评审(pending_review)  ← AI 提交评审时调用
                 ├─ 评审通过(review_approved)
                 │    └─ 已完成(completed)
                 └─ 评审驳回(review_rejected)
                      └─ 开发中(in_progress)  ← 重新开发
```

AI Agent 典型调用顺序：
1. `get_my_requirements` → 选择需求
2. `get_requirement` → 读取详情
3. `update_requirement_status(action="in_progress")` → 标记开始
4. `sync_tasks(tasks=[...])` → 同步任务拆解
5. 开发执行...
6. `submit_test_record(...)` → 上传测试结果
7. `create_document(...)` → 上传设计文档
8. `sync_tasks(tasks=[{status: "completed", actual_hours: N}, ...])` → 终态同步
9. `update_requirement_status(action="pending_review")` → 提交评审

## 鉴权

MCP Token 通过平台"MCP 配置"页面生成，格式为 Bearer JWT。AI 工具在 `.opencode.json` 或 MCP 配置文件中配置：

```json
{
  "mcpServers": {
    "codeseer": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer <TOKEN>"
      }
    }
  }
}
```

## Skill 安装

通过 `setup_dev_environment` 工具，AI 会将以下内容安装到项目根目录：

- `superpowers/` — Superpowers 技能包（TDD、代码审查等）
- `skills/cs_integration/` — CodeSeer 专属 Skill（cs_setup、cs_start 命令）

安装路径使用 `git rev-parse --show-toplevel` 确定项目根目录，**不安装到全局 `~/.opencode/`**。

## 关键约束

- `sync_tasks` 按 `title` 匹配做 upsert，不删除平台已有任务
- `status` 更新时自动维护 `started_at` / `completed_at` 时间戳
- 文档上传后为草稿状态，需在平台手动"挂载模块"并"归档"才能纳入模块知识库
- MCP Token 与用户身份绑定，`get_my_requirements` 只返回该用户被指派的需求
