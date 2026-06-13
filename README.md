# CodeSeer

> 让 AI 既懂需求，也懂代码——从需求评估到自动开发的完整闭环

## 项目简介

CodeSeer 是一套面向研发团队的 AI 辅助研发平台，由两部分组成：

**1. 需求管理 + 智能分析平台**
产品提交需求后，系统进入多状态工作流，可指派、可拆解、可追踪。
每个需求自动绑定 5 阶段开发（澄清 → 计划 → 执行 → 评审 → 测试），
支持优先级、截止日期、自定义字段、可配置状态机，让团队在开发前就了解
工作量和影响范围。

**2. AI 自动开发工作流（基于 Superpowers 框架）**
平台内置 **MCP Server**，与 [Superpowers](https://github.com/obra/superpowers)
的 AI 开发流程框架深度集成。研发在 Claude Code / Cursor 中可直接拉取
已分析的需求，自动完成
**需求澄清 → 创建分支 → 任务拆分 → TDD 编码 → 代码审查 → 文档同步**
的全流程。平台强制流程节点：TDD 三态（Red / Green / Refactor）必须
按顺序提交、代码审查未通过不能进入测试阶段、文档不归档不算完成。

两者共享同一套 **项目知识库（模块 Skill 仓库）**——每个模块都有对应的
Skill 文件，描述模块设计、归档文档要点、常见陷阱。需求分析阶段用它
辅助影响范围判断，文档归档时自动聚合成 Skill，开发阶段反向指导 AI
写出符合团队规范的代码。

## 核心特性

- 📋 **需求 → 全流程追踪**：多状态工作流 + 5 阶段开发 + 自定义字段 + 可配置状态机
- 🤖 **AI 协同开发**：MCP + Superpowers 框架接入 AI 编码工具，强制 TDD + 自动代码审查
- 🧠 **模块 Skill 仓库**：迭代发布后自动归档文档 → 聚合生成领域专家 Prompt
- 📚 **团队规范自动接入**：Skill 库作为 AI 启动开发前的标准上下文加载
- 🔄 **Webhook 事件流**：8 类业务事件 + HMAC 签名，可对接 Slack / Lark / Jenkins
- 👥 **5 角色权限矩阵**：admin / PM / 项目经理 / 开发 / 只读，资源级权限
- ⏰ **早会视图 + 延期提醒**：按开发者聚合进度，自动标红 due_date 已过的需求
- 🗂 **文档版本化**：Markdown 草稿→自动归档，AI 摘要 + 关键要点提取
- 🔌 **可插拔 MCP**：标准 JSON-RPC 协议，AI 工具即插即用

## 技术架构

### 后端
- **框架**：Python 3.11+ / FastAPI / Uvicorn
- **数据**：SQLAlchemy 2.0 (async) + aiosqlite（可平滑切换 PostgreSQL）
- **校验**：Pydantic v2
- **集成**：aiohttp（Webhook 异步投递）/ hmac（HMAC-SHA256 签名）

### 前端
- **框架**：Vue 3 / TypeScript / Vite
- **路由**：Vue Router 4
- **请求**：Axios

### MCP 协同层
- **Server**：Node.js + @modelcontextprotocol/sdk
- **协议**：JSON-RPC over stdio / HTTP
- **接入方**：Claude Code、Cursor 等支持 MCP 的 AI 编码工具

### 数据存储
- **数据库**：SQLite（开箱即用）
- **文件**：文档内容 + Skill Prompt 以 Markdown / 文本形式存储于 SQLite

## 核心功能模块

按 4 个优先级组织：

### 🟢 P0 基础（必备）
- **需求管理**：多状态工作流、可指派、优先级、截止日期、5 阶段开发
- **文档管理**：草稿→归档自动流转、Markdown 编辑、版本化、AI 摘要与关键要点
- **模块知识库**：模块树、归档文档聚合、**Skill 自动生成**（领域专家 Prompt）

### 🔵 P1 协同（提效）
- **迭代管理**：发布钩子（自动归档草稿文档）、统计、状态分布
- **项目管理**：项目详情、迭代聚合、统计
- **活动日志**：需求全字段变更时间线（创建/指派/状态/阶段/评论）
- **早会视图**：按开发者聚合进度 + **延期提醒**

### 🟡 P2 治理（规范）
- **用户与角色**：5 角色 × 16 资源权限矩阵
- **Webhook 系统**：8 类事件、HMAC-SHA256 签名、异步投递、失败重试、投递记录

### 🟣 P3 灵活（适配）
- **可配置状态机**：数据库持久化、Settings UI 编辑、运行时热生效
- **自定义需求字段**：7 种类型（文本/数字/日期/单选/多选/人员/模块）
- **系统设置页**：状态机 + 自定义字段聚合配置

## 快速开始

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- API 根：`http://localhost:8000/`
- 健康检查：`http://localhost:8000/health`
- OpenAPI 文档：`http://localhost:8000/docs`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`（Vite 已配置 `/api` 代理到 8000）

### 3. 启动 MCP Server（接入 AI 编码工具）

```bash
cd mcp-server
npm install
node index.js
```

在 Claude Code / Cursor 的 MCP 配置中添加 CodeSeer Server，即可通过
MCP 协议同步需求、任务、测试结果。

## 项目结构

```
CodeSeer/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── api/                    # 10 个路由模块
│   │   │   ├── projects.py         # 项目 CRUD + 统计
│   │   │   ├── iterations.py       # 迭代 + 发布 + 统计
│   │   │   ├── requirements.py     # 需求 + 状态机 + 阶段 + 历史
│   │   │   ├── tasks.py            # 任务 + TDD 周期
│   │   │   ├── documents.py        # 文档 + 版本 + 归档
│   │   │   ├── modules.py          # 模块树 + Skill 生成
│   │   │   ├── webhooks.py         # Webhook + 异步分发
│   │   │   ├── users.py            # 用户 + 角色权限
│   │   │   ├── config.py           # 状态机 + 自定义字段
│   │   │   └── mcp.py              # MCP 同步端点
│   │   ├── core/                   # 配置 / 数据库
│   │   ├── models/                 # SQLAlchemy ORM
│   │   └── schemas/                # Pydantic schemas
│   ├── requirements.txt
│   └── codeseer.db                 # SQLite (自动生成)
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── views/                  # 14 个页面
│   │   ├── api/index.ts            # 9 个 API 模块
│   │   ├── router/index.ts         # 14 条路由
│   │   └── assets/                 # 全局样式
│   └── package.json
├── mcp-server/                     # MCP Server (Node.js)
├── docs/                           # 设计文档
└── README.md
```

## 许可证

MIT
