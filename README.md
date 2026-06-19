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

需求分析完成后，将状态推进到 `assigned`，在**负责人**字段指定对应开发者。开发者在 AI 工具中启动工作流时会看到该需求。

### 4. 追踪进度

- **早会视图**：按开发者聚合进度，延期需求自动标红
- **需求详情**：查看任务拆解、TDD 三阶段进度、测试结果
- **活动日志**：全字段变更时间线

---

## 开发者使用流程

### 第 1 步：接入 AI 工具

在你的 AI 编码工具中配置 CodeSeer MCP（只需配置一次）：

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

---

### 第 2 步：初始化开发环境（首次使用）

MCP 连接成功后，在 AI 工具中直接说：

```
初始化 CodeSeer
```

也可以说：`安装 CodeSeer 环境` / `cs 初始化` / `cs setup`

AI 会自动完成：
1. 检查并安装 [Superpowers](https://github.com/obra/superpowers) 技能包
2. 拉取并写入最新的 CodeSeer 专属技能和命令到当前项目目录

安装完成后会出现三个命令：

| 命令 | 说明 |
|------|------|
| `/cs_setup` | 重新安装或更新 CodeSeer 技能和命令 |
| `/cs_start` | 启动 AI 开发工作流 |
| `/cs_doc` | 手动上传文档到平台 |

> **之后更新**，直接运行 `/cs_setup` 即可。

---

### 第 3 步：开始开发（/cs_start）

在 AI 工具中说：

```
我要开始工作
```

或输入 `/cs_start`，AI 引导你完成以下流程：

#### 3.1 选择工作目标

AI 自动拉取分配给你的数据，依次选择：

```
选项目 → 选迭代 → 选需求
```

#### 3.2 需求分析阶段（自动）

选定需求后，AI 自动：
1. 调用 **Superpowers brainstorming** 技能进行需求澄清和设计
   - 产出：设计文档，保存在 `docs/cs/<迭代名>/<需求名>/specs/`
2. 调用 **Superpowers writing-plans** 技能拆解实现任务
   - 产出：计划文档，保存在 `docs/cs/<迭代名>/<需求名>/plans/`
   - ⚠️ 每个任务必须包含显式 TDD 步骤（RED→GREEN→REFACTOR），否则计划不完整

#### 3.3 自动同步到平台（无需手动触发）

writing-plans 完成后，AI 立即依次执行：
- 上传设计文档 → 上传计划文档 → 同步任务列表

同步成功后会看到：

```
✅ 设计文档、计划文档和任务已同步到 CodeSeer 平台
```

#### 3.4 TDD 开发阶段（强制）

> ⚠️ TDD 是强制的，不是可选的。所有实现任务必须经过 RED → GREEN → REFACTOR 三个阶段。

每个任务的执行节奏：

| 阶段 | 操作 | 上报到平台 |
|------|------|-----------|
| 开始 | 标记任务为进行中 | `update_task_status(in_progress)` |
| **RED** | 写失败测试 → 运行确认失败 | `submit_test_result(tdd_phase="red")` |
| **GREEN** | 写最小实现 → 运行确认全通过 | `submit_test_result(tdd_phase="green")` |
| **REFACTOR** | 重构 → 确认仍全绿 | `submit_test_result(tdd_phase="refactor")` |
| 完成 | 标记任务为已完成 | `update_task_status(completed)` |

所有任务完成后，推进需求状态到 `pending_review`（待代码评审）。

---

### 手动上传文档（/cs_doc）

如需在工作流之外单独上传文档，运行：

```
/cs_doc
```

或指定文档类型：

```
/cs_doc design    # 上传设计文档
/cs_doc plan      # 上传计划文档
/cs_doc api       # 上传 API 文档
/cs_doc other     # 上传其他文档
```

不带参数时 AI 会显示类型选择菜单，然后引导你：
1. 选择关联的需求
2. 从对应目录（`docs/cs/<迭代名>/<需求名>/specs|plans|api/`）读取文件，或手动粘贴内容
3. 上传并告知结果

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
| `review_rejected` | 评审驳回，重新开发 |
| `completed` | 已完成 |

---

## 文档目录结构

AI 工作流产出的文档统一按迭代和需求归档：

```
docs/cs/
└── <迭代名>/
    └── <需求名>/
        ├── specs/    # 设计文档（brainstorming 产出）
        ├── plans/    # 计划文档（writing-plans 产出）
        └── api/      # API 文档
```

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
