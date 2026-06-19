# 技术文档

## 技术架构

### 后端
- **框架**：Python 3.11+ / FastAPI / Uvicorn
- **数据**：SQLAlchemy 2.0 (async) + aiosqlite（可平滑切换 PostgreSQL）
- **校验**：Pydantic v2
- **认证**：JWT（python-jose）+ bcrypt 密码哈希
- **集成**：aiohttp（Webhook 异步投递）/ hmac（HMAC-SHA256 签名）

### 前端
- **框架**：Vue 3 / TypeScript / Vite
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **请求**：Axios（JWT 拦截器 + 401 自动跳转登录）

### MCP 协同层
- **Server**：FastAPI HTTP MCP（JSON-RPC 2.0 over HTTP）
- **协议**：标准 MCP 协议，支持 `initialize` / `tools/list` / `tools/call`
- **接入方**：Claude Code、OpenCode、Cursor 等支持 MCP 的 AI 编码工具
- **认证**：Bearer Token（Access Token，在 Web 界面申请）
- **自动初始化**：`initialize` 握手时下发 `/setup_cs_env` 斜杠命令到项目目录

### 数据存储
- **数据库**：SQLite（开箱即用，可切换 PostgreSQL）
- **文件**：文档内容 + Skill Prompt 以 Markdown / 文本形式存储于 SQLite

---

## 项目结构

```
CodeSeer/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── api/                    # 路由模块
│   │   │   ├── projects.py         # 项目 CRUD + 统计
│   │   │   ├── iterations.py       # 迭代 + 发布 + 统计
│   │   │   ├── requirements.py     # 需求 + 状态机 + 阶段 + 历史
│   │   │   ├── tasks.py            # 任务 + TDD 周期
│   │   │   ├── documents.py        # 文档 + 版本 + 归档
│   │   │   ├── modules.py          # 模块树 + Skill 生成
│   │   │   ├── webhooks.py         # Webhook + 异步分发
│   │   │   ├── users.py            # 用户 + 角色权限
│   │   │   ├── auth.py             # 登录 / JWT
│   │   │   ├── mcp_http.py         # MCP HTTP 端点
│   │   │   └── mcp_tokens.py       # Access Token 管理
│   │   ├── core/                   # 配置 / 数据库 / 认证
│   │   ├── models/                 # SQLAlchemy ORM
│   │   └── schemas/                # Pydantic schemas
│   └── tests/                      # pytest 测试套件
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── views/                  # 页面组件
│   │   ├── stores/                 # Pinia 状态（auth）
│   │   ├── api/index.ts            # API 模块
│   │   └── router/index.ts         # 路由 + 权限守卫
├── aicode/                         # AI 编码工具集成资源
│   ├── skills/
│   │   └── codeseer-integration.md # CodeSeer 专属技能
│   └── commands/
│       └── setup_cs_env.md         # /setup_cs_env 斜杠命令
├── docs/                           # 文档
└── README.md
```

---

## 启动方式

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API 根：`http://localhost:8000/`
- OpenAPI 文档：`http://localhost:8000/docs`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`（Vite 已配置 `/api` 代理到 8000）

---

## MCP 工具清单

| 工具 | 说明 |
|------|------|
| `setup_dev_environment` | 返回 superpowers 安装指令 + CodeSeer 专属技能内容 |
| `list_my_projects` | 列出当前开发者有未完成需求的项目 |
| `list_iterations` | 列出指定项目的迭代 |
| `list_my_requirements` | 列出指定迭代中分配给当前开发者的需求 |
| `start_brainstorming` | 锁定需求，返回完整上下文（描述、验收标准、任务、测试记录） |
| `get_requirement_detail` | 获取需求完整详情（含任务列表） |
| `sync_tasks` | 将 AI 拆解的任务列表同步到平台 |
| `update_requirement_status` | 触发需求状态流转 |
| `update_task_status` | 更新单个任务状态和 TDD 进度 |
| `submit_test_result` | 提交单元测试执行结果 |

---

## 需求状态流转

```
draft → pending_analysis → analyzed → assigned → claimed → in_progress
     → pending_review → review_approved → completed
                      ↘ review_rejected → in_progress
```

## 角色权限矩阵

| 角色 | 说明 |
|------|------|
| admin | 超级管理员，管理用户和系统配置 |
| pm | 产品经理，创建需求、管理迭代 |
| project_manager | 项目经理，分配需求、追踪进度 |
| developer | 开发者，认领需求、接入 AI 工具开发 |
| viewer | 只读，查看项目和需求 |
