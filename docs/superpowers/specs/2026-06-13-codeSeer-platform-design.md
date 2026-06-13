# CodeSeer 平台设计文档

## 一、项目概述

### 1.1 项目定位

CodeSeer 是一个 AI 编码流程平台，旨在为团队提供从需求管理到代码开发的一站式协作平台。平台连接产品经理和开发人员，通过 AI 能力辅助需求分析、文档管理和知识积累。

### 1.2 目标用户

- **产品经理**：上传需求、查看分析结果、指派任务
- **开发人员**：通过 ClaudeCode 接入平台，领取和完成开发任务
- **项目经理**：管理团队、监控进度、协调资源
- **管理员**：系统配置、权限管理

### 1.3 设计原则

- **可扩展性**：平台核心逻辑可扩展，支持插件、Webhook、自定义字段
- **模块化**：各模块职责清晰，通过接口通信
- **自动化**：AI 自动分析需求、整理文档、生成 Skill
- **多租户支持**：架构预留多租户能力

---

## 二、核心流程

```
┌─────────────────────────────────────────────────────────────────┐
│                         产品端                                   │
│  上传需求 → 自动Skill分析 → 指派给开发                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         平台端                                   │
│  需求管理（可配置状态机）                                        │
│  文档管理（草稿 → 正式归档）                                      │
│  模块知识库（文档积累）                                          │
│  Skill生成（新模块自动生成，老模块动态引用）                      │
│  Webhook（全事件触发）                                          │
│  MCP服务（ClaudeCode双向通信）                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       ClaudeCode                                │
│  通过MCP拉取需求 → 使用Superpower流程 → 完成后提交文档           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 流程说明

1. **产品上传需求**
   - 产品经理填写需求信息（标题、描述、验收标准、优先级等）
   - 需求创建后进入草稿状态

2. **自动 Skill 分析**
   - 需求提交后自动触发 Skill 分析
   - 分析结果给产品参考：涉及模块、工时估算、技术建议
   - 产品根据分析结果完善需求

3. **需求指派**
   - 产品/项目经理将需求指派给具体开发
   - 指派后开发可通过 MCP 获取任务

4. **开发完成任务**
   - 开发通过 ClaudeCode MCP 拉取指派给自己的需求
   - 使用 Superpower 流程进行开发
   - 完成后通过 MCP 提交设计文档到平台

5. **文档归档与 Skill 生成**
   - 开发提交文档 → 草稿状态
   - 版本上线 → 文档正式归档 → AI 整理
   - 新模块：自动生成 Skill
   - 老模块：Skill 动态引用文档

---

## 三、功能模块详细设计

### 3.1 需求管理模块

#### 3.1.1 需求实体设计

```yaml
需求:
  id: UUID
  title: String (必填, 最大200字符)
  description: Text (As a... I want... so that...)
  acceptance_criteria: List[Text] (验收标准列表)
  project_id: UUID (关联项目)
  iteration_id: UUID (关联迭代/版本)
  status: Enum (状态)
  priority: Enum (P0/P1/P2/P3)
  assignee_id: UUID (指派给开发)
  creator_id: UUID (创建人)
  estimated_hours:
    min: Decimal
    max: Decimal
    confidence: Float
  actual_hours: Decimal
  due_date: Date
  custom_fields: JSON (动态字段)
  created_at: DateTime
  updated_at: DateTime
```

#### 3.1.2 需求状态机（可配置）

```yaml
默认状态流转:
  - state: draft
    name: 草稿
    description: 需求创建，尚未提交分析
    allowed_transitions:
      - pending_analysis

  - state: pending_analysis
    name: 待分析
    description: 等待Skill分析中
    allowed_transitions:
      - analyzed

  - state: analyzed
    name: 已分析
    description: Skill分析完成，待指派
    allowed_transitions:
      - assigned

  - state: assigned
    name: 已指派
    description: 已指派给开发，待领取
    allowed_transitions:
      - claimed
      - analyzed

  - state: claimed
    name: 已领取
    description: 开发已领取，开发中
    allowed_transitions:
      - in_progress
      - unclaimed

  - state: in_progress
    name: 开发中
    description: 正在进行开发
    allowed_transitions:
      - pending_review
      - paused

  - state: pending_review
    name: 待评审
    description: 开发完成，待评审
    allowed_transitions:
      - review_approved
      - review_rejected

  - state: review_approved
    name: 评审通过
    description: 评审通过
    allowed_transitions:
      - completed

  - state: review_rejected
    name: 评审驳回
    description: 评审未通过
    allowed_transitions:
      - in_progress

  - state: completed
    name: 已完成
    description: 需求完成
    allowed_transitions: []
```

#### 3.1.3 动态字段配置

```yaml
字段定义:
  - field_key: String (唯一标识)
    field_name: String (显示名称)
    field_type: 
      - text
      - number
      - date
      - datetime
      - select
      - multiselect
      - user
      - module
    required: Boolean
    options: List[String] (当下拉类型时)
    default_value: Any
```

#### 3.1.4 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/requirements` | POST | 创建需求 |
| `/api/requirements` | GET | 查询需求列表（支持多条件筛选） |
| `/api/requirements/:id` | GET | 获取需求详情 |
| `/api/requirements/:id` | PUT | 更新需求 |
| `/api/requirements/:id` | DELETE | 删除需求 |
| `/api/requirements/:id/assign` | POST | 指派需求 |
| `/api/requirements/:id/claim` | POST | 领取需求 |
| `/api/requirements/:id/transition` | POST | 状态流转 |
| `/api/requirements/:id/history` | GET | 状态变更历史 |
| `/api/requirements/status-config` | GET | 获取状态流转配置 |
| `/api/requirements/status-config` | PUT | 更新状态流转配置 |
| `/api/requirements/by-project/:project_id` | GET | 获取项目下所有需求 |
| `/api/requirements/by-iteration/:iteration_id` | GET | 获取迭代下所有需求 |

---

### 3.2 Skill 分析模块

#### 3.2.1 Skill 定义

```yaml
Skill:
  id: UUID
  name: String
  version: String
  description: Text
  provider: Enum (anthropic_mcp/custom_mcp/openapi)
  endpoint: String (服务地址)
  config: JSON
  enabled: Boolean
  created_at: DateTime
  updated_at: DateTime
```

#### 3.2.2 分析任务

```yaml
AnalysisTask:
  id: UUID
  requirement_id: UUID
  skill_id: UUID
  status: Enum (pending/running/completed/failed)
  input: JSON
  output: JSON
  error: Text
  started_at: DateTime
  completed_at: DateTime
```

#### 3.2.3 分析输出结构

```yaml
AnalysisOutput:
  modules: List[ModuleAnalysis]
    - module_id: UUID
      name: String
      impact_level: Enum (high/medium/low)
      confidence: Float
      
  estimated_hours:
    min: Float
    max: Float
    confidence: Float
    
  related_documents:
    - document_id: UUID
      relevance: Float
      
  suggestions:
    - type: Enum (clarification/technical/estimation)
      content: Text
      priority: Integer
```

#### 3.2.4 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/skills` | GET | 获取可用Skills列表 |
| `/api/skills` | POST | 注册自定义Skill |
| `/api/skills/:id` | GET | 获取Skill详情 |
| `/api/skills/:id` | PUT | 更新Skill配置 |
| `/api/skills/:id` | DELETE | 删除Skill |
| `/api/requirements/:id/analyze` | POST | 触发需求分析 |
| `/api/requirements/:id/analysis` | GET | 获取分析结果 |

---

### 3.3 MCP 服务模块

#### 3.3.1 MCP 资源定义

```yaml
MCP资源:
  - requirements: list, get, update_status
  - documents: submit, get, list
  - modules: list, get, get_knowledge
```

#### 3.3.2 MCP Tools

```yaml
MCP Tools:
  # 需求相关
  - name: list_assigned_requirements
    description: 获取指派给当前开发的所有需求
    input:
      filters: JSON (可选筛选条件)
    output:
      requirements: List[Requirement]

  - name: get_requirement_detail
    description: 获取需求详情
    input:
      requirement_id: String
      include_analysis: Boolean
      include_documents: Boolean
      include_tasks: Boolean
      include_test_records: Boolean
    output:
      requirement: Requirement
      analysis: AnalysisOutput
      tasks: List[Task]
      test_records: List[UnitTestRecord]

  - name: update_requirement_status
    description: 更新需求状态
    input:
      requirement_id: String
      action: String
      comment: String
    output:
      success: Boolean

  # 任务相关
  - name: sync_tasks
    description: 同步任务列表到平台（Superpower任务拆分后调用）
    input:
      requirement_id: String
      phases: JSON (阶段状态)
      tasks: List[Task]
    output:
      success: Boolean
      requirement_id: String

  - name: update_task_status
    description: 更新任务状态
    input:
      requirement_id: String
      task_id: String
      status: String
      tdd_cycle: JSON
      actual_hours: Decimal
      notes: String
    output:
      success: Boolean
      task: Task

  # 测试相关
  - name: submit_test_result
    description: 提交单元测试结果
    input:
      requirement_id: String
      task_id: String
      test_type: String
      total_count: Integer
      passed_count: Integer
      failed_count: Integer
      failed_tests: List[FailedTest]
      coverage: Float
      result: String
      executed_at: DateTime
    output:
      success: Boolean
      test_record_id: String

  # 文档相关
  - name: submit_design_document
    description: 提交设计文档
    input:
      requirement_id: String
      document_type: Enum
      file_name: String
      content: String (Base64)
      metadata: JSON
    output:
      document_id: String
      status: String

  # 模块相关
  - name: get_module_context
    description: 获取模块上下文用于分析
    input:
      module_id: String
      purpose: String
    output:
      documents: List[Document]
      skill_id: String
```

#### 3.3.3 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/mcp/requirements` | GET | 获取指派给自己的需求 |
| `/api/mcp/requirements/:id` | GET | 获取需求详情 |
| `/api/mcp/requirements/:id/status` | POST | 更新需求状态 |
| `/api/mcp/modules/:id/context` | GET | 获取模块上下文 |

---

### 3.4 文档管理模块

#### 3.4.1 文档实体设计

```yaml
Document:
  id: UUID
  requirement_id: UUID
  module_id: UUID (归档时关联)
  version_id: UUID (归档时关联)
  title: String
  document_type: Enum (analysis/design/diagram/other)
  file_path: String
  file_size: Integer
  file_hash: String
  status: Enum (draft/archived/deprecated)
  processing:
    status: Enum (pending/processing/completed/failed)
    summary: Text
    key_points: List[String]
    relevant_modules: List[UUID]
  created_by: UUID
  created_at: DateTime
  archived_at: DateTime
```

#### 3.4.2 文档状态流转

```
[draft] ─── 版本上线 ───→ [archived]
    │                         │
    ↓                         ↓
[deprecated] ←── 废弃 ←─── [archived]
```

#### 3.4.3 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/documents` | POST | 上传文档 |
| `/api/documents` | GET | 查询文档列表 |
| `/api/documents/:id` | GET | 获取文档详情 |
| `/api/documents/:id` | PUT | 更新文档 |
| `/api/documents/:id` | DELETE | 删除文档 |
| `/api/documents/:id/archive` | POST | 归档文档 |
| `/api/documents/:id/process` | POST | 触发AI整理 |
| `/api/documents/:id/versions` | GET | 获取文档版本历史 |

---

### 3.5 模块知识库模块

#### 3.5.1 模块实体设计

```yaml
Module:
  id: UUID
  name: String
  description: Text
  parent_id: UUID (父模块，支持层级)
  level: Integer
  path: String (层级路径，如: /order/create)
  skill_id: UUID
  document_count: Integer
  requirement_count: Integer
  created_by: UUID
  created_at: DateTime
  is_active: Boolean
```

#### 3.5.2 层级模块示例

```
├── order (订单系统)
│   ├── order/create (订单创建)
│   ├── order/query (订单查询)
│   └── order/cancel (订单取消)
├── user (用户中心)
│   ├── user/auth (用户认证)
│   └── user/profile (用户资料)
└── payment (支付服务)
```

#### 3.5.3 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/modules` | GET | 获取模块树 |
| `/api/modules` | POST | 创建模块 |
| `/api/modules/:id` | GET | 获取模块详情 |
| `/api/modules/:id` | PUT | 更新模块 |
| `/api/modules/:id` | DELETE | 删除模块 |
| `/api/modules/:id/documents` | GET | 获取模块下文档 |
| `/api/modules/:id/knowledge` | GET | 获取模块知识库 |
| `/api/modules/:id/generate-skill` | POST | 生成模块Skill |

---

### 3.6 Skill 自动生成模块

#### 3.6.1 Skill 实体设计

```yaml
Skill:
  id: UUID
  name: String
  version: String
  module_id: UUID
  source: Enum (auto_generated/manual)
  status: Enum (generating/draft/active/deprecated)
  
  config:
    prompt_template: Text
    model: String
    parameters: JSON
    
  generated_from_documents:
    - document_id: UUID
      weight: Float
      
  created_at: DateTime
```

#### 3.6.2 Skill 生成流程

```
文档正式归档
    ↓
触发Skill生成 [generating]
    ↓
提取文档关键信息
    ↓
构建Prompt模板
    ↓
生成Skill配置 [draft]
    ↓
内部测试
    ↓
[active]
```

#### 3.6.3 老模块动态引用机制

```yaml
Skill引用配置:
  module_id: UUID
  skill_id: UUID
  skill_type: dynamic
  
  dynamic_config:
    reference_strategy:
      - type: recent
        count: 10
      - type: relevant
        threshold: 0.7
      - type: all
        
    context_mode:
      - full
      - summary
      - key_points
```

---

### 3.7 Webhook 模块

#### 3.7.1 Webhook 事件定义

```yaml
事件类型:
  requirement:
    - created
    - updated
    - deleted
    - assigned
    - claimed
    - status_changed
    
  document:
    - submitted
    - processed
    - archived
    - deprecated
    
  module:
    - created
    - updated
    - skill_generated
    
  skill:
    - created
    - activated
    - deprecated
    
  system:
    - version_released
```

#### 3.7.2 Webhook 配置

```yaml
WebhookConfig:
  id: UUID
  name: String
  url: String
  secret: String
  events: List[String]
  enabled: Boolean
  retry_policy:
    max_retries: Integer
    retry_interval: Integer
    timeout: Integer
```

#### 3.7.3 签名验证

```
X-CodeSeer-Signature: sha256=hmac_sha256(secret, payload)
```

#### 3.7.4 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/webhooks` | GET | 获取Webhook列表 |
| `/api/webhooks` | POST | 创建Webhook |
| `/api/webhooks/:id` | GET | 获取Webhook详情 |
| `/api/webhooks/:id` | PUT | 更新Webhook |
| `/api/webhooks/:id` | DELETE | 删除Webhook |
| `/api/webhooks/:id/test` | POST | 发送测试事件 |
| `/api/webhooks/:id/deliveries` | GET | 获取投递记录 |

---

### 3.8 权限模块

#### 3.8.1 角色定义

```yaml
角色:
  - role: admin
    name: 管理员
    permissions: ["*"]
    
  - role: product_manager
    name: 产品经理
    permissions:
      - requirements:create
      - requirements:edit_own
      - requirements:delete_own
      - requirements:assign
      - modules:view
      
  - role: project_manager
    name: 项目经理
    permissions:
      - requirements:view
      - requirements:edit
      - requirements:assign
      - requirements:view_all
      - modules:manage
      - users:manage
      
  - role: developer
    name: 开发
    permissions:
      - requirements:view_assigned
      - requirements:claim
      - requirements:update_status
      - documents:submit
      - modules:view
      - skills:view
      
  - role: viewer
    name: 访客
    permissions:
      - requirements:view_public
      - modules:view
```

#### 3.8.2 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/roles` | GET | 获取角色列表 |
| `/api/roles/:id/permissions` | PUT | 更新角色权限 |
| `/api/users` | GET | 获取用户列表 |
| `/api/users` | POST | 创建用户 |
| `/api/users/:id` | PUT | 更新用户 |
| `/api/users/:id/roles` | PUT | 分配用户角色 |

---

### 3.9 项目管理模块

#### 3.9.1 项目实体设计

```yaml
Project:
  id: UUID
  name: String
  description: Text
  status: Enum (active/archived/completed)
  owner_id: UUID (项目负责人)
  created_by: UUID
  created_at: DateTime
  updated_at: DateTime
```

#### 3.9.2 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET | 获取项目列表 |
| `/api/projects` | POST | 创建项目 |
| `/api/projects/:id` | GET | 获取项目详情 |
| `/api/projects/:id` | PUT | 更新项目 |
| `/api/projects/:id` | DELETE | 删除项目 |
| `/api/projects/:id/iterations` | GET | 获取项目下所有迭代 |
| `/api/projects/:id/statistics` | GET | 获取项目统计数据 |

---

### 3.10 迭代管理模块

> 注：迭代（Iteration）即版本（Version），两者等价

#### 3.10.1 迭代实体设计

```yaml
Iteration:
  id: UUID
  project_id: UUID (所属项目)
  name: String (如: v1.0.0, 2024-Q2-Sprint1)
  description: Text
  status: Enum (planning/development/testing/released/archived)
  planned_release_date: Date
  actual_release_date: Date
  requirement_count: Integer
  completed_count: Integer
  created_by: UUID
  created_at: DateTime
  updated_at: DateTime
```

#### 3.10.2 迭代状态流转

```
[planning] → [development] → [testing] → [released]
     ↓              ↓              ↓           ↓
  [archived]    [archived]    [archived]  [archived]
```

#### 3.10.3 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/iterations` | GET | 获取迭代列表 |
| `/api/iterations` | POST | 创建迭代 |
| `/api/iterations/:id` | GET | 获取迭代详情 |
| `/api/iterations/:id` | PUT | 更新迭代 |
| `/api/iterations/:id` | DELETE | 删除迭代 |
| `/api/iterations/:id/release` | POST | 发布迭代 |
| `/api/iterations/:id/requirements` | GET | 获取迭代下的需求 |
| `/api/iterations/:id/statistics` | GET | 获取迭代统计数据 |

---

### 3.11 需求与项目/迭代关系

#### 3.11.1 关系结构

```
项目 (Project)
  └── 迭代 (Iteration) = 版本 (Version)
        └── 需求 (Requirement)
```

#### 3.11.2 需求实体更新

```yaml
需求:
  id: UUID
  title: String
  description: Text
  acceptance_criteria: List[Text]
  iteration_id: UUID (关联迭代，即版本)
  project_id: UUID (关联项目)
  status: Enum
  priority: Enum
  assignee_id: UUID
  creator_id: UUID
  estimated_hours:
    min: Decimal
    max: Decimal
    confidence: Float
  actual_hours: Decimal
  due_date: Date
  custom_fields: JSON
  created_at: DateTime
  updated_at: DateTime
```

---

### 3.12 任务管理模块

#### 3.12.1 任务实体设计

```yaml
Task:
  id: UUID
  requirement_id: UUID (关联需求)
  title: String (任务标题)
  description: Text (任务描述)
  status: Enum (pending/in_progress/completed/blocked)
  priority: Enum (P0/P1/P2/P3)
  order: Integer (任务顺序)
  estimated_hours: Decimal
  actual_hours: Decimal
  tdd_cycle:
    red:
      status: Enum (pending/in_progress/completed)
      completed_at: DateTime
    green:
      status: Enum (pending/in_progress/completed)
      completed_at: DateTime
    refactor:
      status: Enum (pending/in_progress/completed)
      completed_at: DateTime
  started_at: DateTime
  completed_at: DateTime
  metadata: JSON (Superpower传递的额外信息)
  created_at: DateTime
  updated_at: DateTime
```

#### 3.12.2 需求阶段实体设计

```yaml
RequirementPhase:
  id: UUID
  requirement_id: UUID
  phase: Enum
    - clarification     # 需求澄清
    - planning         # 任务规划
    - execution        # 任务执行
    - review           # 代码审查
    - testing          # 单元测试
  status: Enum (pending/in_progress/completed)
  started_at: DateTime
  completed_at: DateTime
  notes: Text
```

#### 3.12.3 单元测试记录实体

```yaml
UnitTestRecord:
  id: UUID
  requirement_id: UUID
  task_id: UUID (关联任务)
  task_title: String (冗余存储，便于展示)
  test_type: Enum (unit/integration/e2e)
  total_count: Integer (总测试数)
  passed_count: Integer (通过数)
  failed_count: Integer (失败数)
  failed_tests: List[FailedTest]
  coverage: Float (覆盖率，可选)
  result: Enum (all_passed/failed/partial)
  executed_at: DateTime
  details: JSON

FailedTest:
  name: String
  task_id: UUID
  message: Text
  stack_trace: Text (可选)
```

#### 3.12.4 MCP 接口设计

**同步任务列表（Superpower → 平台）**

```json
POST /api/mcp/sync-tasks
{
  "requirement_id": "req-uuid-001",
  "phases": {
    "clarification": {"status": "completed", "completed_at": "2024-06-15T09:00:00Z"},
    "planning": {"status": "completed", "completed_at": "2024-06-15T09:30:00Z"},
    "execution": {"status": "in_progress"}
  },
  "tasks": [
    {
      "title": "实现用户注册API",
      "description": "TDD开发：RED→GREEN→REFACTOR",
      "priority": "P1",
      "estimated_hours": 4,
      "order": 1,
      "tdd_cycle": {
        "red": {"status": "completed", "completed_at": "2024-06-15T10:00:00Z"},
        "green": {"status": "completed", "completed_at": "2024-06-15T10:30:00Z"},
        "refactor": {"status": "completed", "completed_at": "2024-06-15T11:00:00Z"}
      }
    },
    {
      "title": "编写数据库迁移脚本",
      "description": "创建users表结构",
      "priority": "P1",
      "estimated_hours": 2,
      "order": 2
    }
  ]
}
```

**更新任务状态**

```json
POST /api/mcp/update-task
{
  "requirement_id": "req-uuid-001",
  "task_id": "task-001",
  "status": "completed",
  "tdd_cycle": {
    "red": {"status": "completed", "completed_at": "2024-06-15T10:00:00Z"},
    "green": {"status": "completed", "completed_at": "2024-06-15T10:30:00Z"},
    "refactor": {"status": "completed", "completed_at": "2024-06-15T11:00:00Z"}
  },
  "actual_hours": 3.5,
  "notes": "API实现完成，包含单元测试"
}
```

**提交单元测试结果**

```json
POST /api/mcp/submit-test-result
{
  "requirement_id": "req-uuid-001",
  "task_id": "task-001",
  "test_type": "unit",
  "total_count": 50,
  "passed_count": 48,
  "failed_count": 2,
  "failed_tests": [
    {"name": "test_user_phone_validation", "message": "边界条件未处理"},
    {"name": "test_duplicate_phone", "message": "未正确返回错误码"}
  ],
  "coverage": 85.5,
  "result": "partial",
  "executed_at": "2024-06-15T11:00:00Z"
}
```

#### 3.12.5 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/requirements/:id/tasks` | GET | 获取需求下所有任务 |
| `/api/requirements/:id/tasks` | POST | 批量创建任务（Superpower同步） |
| `/api/requirements/:id/tasks/:task_id` | PUT | 更新任务状态 |
| `/api/requirements/:id/tasks/:task_id` | DELETE | 删除任务 |
| `/api/requirements/:id/phases` | GET | 获取需求阶段状态 |
| `/api/requirements/:id/phases` | PUT | 更新需求阶段状态 |
| `/api/requirements/:id/test-records` | GET | 获取所有测试记录 |
| `/api/requirements/:id/test-records` | POST | 提交测试结果 |
| `/api/requirements/:id/test-summary` | GET | 获取测试汇总统计 |
| `/api/mcp/sync-tasks` | POST | MCP同步任务列表 |
| `/api/mcp/update-task` | POST | MCP更新任务状态 |
| `/api/mcp/submit-test-result` | POST | MCP提交测试结果 |

#### 3.12.6 需求详情页展示

```
需求：用户登录功能
状态：开发中
进度：60%
迭代：v1.0.0 - Sprint 2
指派给：张三

开发阶段：
☑ 需求澄清 (完成 - 09:00)
☑ 任务规划 (完成 - 09:30)
◐ 任务执行 (进行中 - 2/4任务完成)
○ 代码审查 (待开始)
○ 单元测试 (待开始)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
任务列表 (4个任务)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌────┬──────────────────────┬──────────┬──────────────────────┬────────────┐
│ #  │ 任务名称              │ 状态     │ TDD进度              │ 完成时间   │
├────┼──────────────────────┼──────────┼──────────────────────┼────────────┤
│ 1  │ 实现用户注册API       │ ✅ 完成  │ ✓→✓→✓              │ 11:00     │
│ 2  │ 编写数据库迁移脚本    │ ✅ 完成  │ ✓→✓→✓              │ 11:30     │
│ 3  │ 实现登录API           │ 🔄 进行中 │ ✓→✓→○              │ -         │
│ 4  │ 前端登录页面          │ ○ 待开始 │ -                   │ -         │
└────┴──────────────────────┴──────────┴──────────────────────┴────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
单元测试记录 (2条记录)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────┬────────┬──────┬───────┬────────┬──────────┬──────────┐
│ 关联任务             │ 类型   │ 总数 │ 通过  │ 失败   │ 覆盖率  │ 结果     │
├──────────────────────┼────────┼──────┼───────┼────────┼──────────┼──────────┤
│ 实现用户注册API      │ 单元   │  50  │   48  │   2    │  85.5%   │ ❌部分通过│
│ 编写数据库迁移脚本   │ 单元   │  20  │   20  │   0    │  90.0%   │ ✅全部通过│
├──────────────────────┼────────┼──────┼───────┼────────┼──────────┼──────────┤
│ 汇总                 │ -      │  70  │   68  │   2    │  87.0%   │ ❌部分通过│
└──────────────────────┴────────┴──────┴───────┴────────┴──────────┴──────────┘

失败的测试用例：
├─ test_user_phone_validation (注册API)
│   └─ 边界条件未处理
├─ test_duplicate_phone (注册API)
│   └─ 未正确返回错误码
```

---

### 3.13 多租户支持（预留）

#### 3.13.1 租户实体

```yaml
Tenant:
  id: UUID
  name: String
  slug: String
  settings: JSON
  plan: Enum (free/pro/enterprise)
  created_at: DateTime
```

---

## 四、扩展能力

### 4.1 Webhook 全事件触发

所有以下事件均可触发 Webhook：

- **需求事件**：created, updated, deleted, assigned, claimed, status_changed
- **文档事件**：submitted, processed, archived, deprecated
- **模块事件**：created, updated, skill_generated
- **Skill事件**：created, activated, deprecated
- **系统事件**：version_released

### 4.2 状态机可配置

- 管理员可自定义状态和流转规则
- 每个状态可配置允许的后续状态
- 状态变更触发 Webhook

### 4.3 数据结构可扩展

- 支持自定义需求字段
- 支持多种字段类型：text, number, date, select, multiselect, user, module
- 字段可配置必填/可选

### 4.4 Skill Hub 对接

- 支持对接 Anthropic MCP Hub
- 支持自定义 MCP 服务
- 支持 OpenAPI 兼容服务

### 4.5 Skill 自动生成

- 新模块文档归档后自动生成 Skill
- 老模块 Skill 动态引用文档
- Skill 质量可评估

---

## 五、技术架构建议

### 5.1 技术栈

- **后端**：Python / FastAPI
- **前端**：Vue 3 + TypeScript
- **数据库**：PostgreSQL
- **文件存储**：本地存储/S3兼容对象存储
- **缓存**：Redis
- **消息队列**：RabbitMQ/Redis Queue

### 5.2 部署方式

- 私有化部署
- 支持 Docker/Kubernetes

### 5.3 核心架构

```
┌─────────────────────────────────────────┐
│                  Web UI                  │
└─────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│               API Gateway                │
│         (认证、限流、路由)               │
└─────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│              FastAPI Backend            │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 需求服务  │ │ 文档服务  │ │ Skill服务│ │
│  └──────────┘ └──────────┘ └─────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Webhook  │ │ 权限服务  │ │ 版本服务 │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│              PostgreSQL                  │
└─────────────────────────────────────────┘
```

### 5.4 MCP 服务架构

```
┌─────────────────────────────────────────┐
│              ClaudeCode                  │
│           (MCP Client)                   │
└─────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│         CodeSeer MCP Server             │
│  ┌──────────────────────────────────┐  │
│  │  Resources: requirements,        │  │
│  │            documents, modules    │  │
│  │  Tools: list, get, submit,       │  │
│  │         update_status            │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│              Backend API                │
└─────────────────────────────────────────┘
```

---

## 六、前端设计

### 6.1 设计规范

#### 6.1.1 技术选型

- **框架**：Vue 3 + TypeScript
- **UI 风格**：简洁专业（Linear/Jira 风格）
- **布局**：侧边栏导航 + 右侧内容区
- **响应式**：PC 优先

#### 6.1.2 页面优先级

1. 工作台（优先开发）
2. 需求列表/详情页
3. 迭代管理页面
4. 项目管理页面
5. 早会跟进视图
6. MCP 配置页面
7. 管理后台（权限、Webhook等）

### 6.2 整体布局

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Logo   │  工作台  │  需求  │  迭代  │  项目  │  早会  │  MCP配置  │ [头像]│
├─────────┴─────────┴────────┴────────┴────────┴────────┴──────────┴──────┤
│ ┌─────────┐ ┌────────────────────────────────────────────────────────────┐ │
│ │         │ │                                                            │ │
│ │ 侧边栏   │ │                      内容区                                │ │
│ │         │ │                                                            │ │
│ │ 🔥 Logo │ │                                                            │ │
│ │ ─────── │ │                                                            │ │
│ │ 📌 工作台│ │                                                            │ │
│ │ 📝 需求  │ │                                                            │ │
│ │ 🔄 迭代 │ │                                                            │ │
│ │ 📁 项目  │ │                                                            │ │
│ │ 📊 早会  │ │                                                            │ │
│ │ 🔧 MCP  │ │                                                            │ │
│ │ ─────── │ │                                                            │ │
│ │ ⚙️ 系统 │ │                                                            │ │
│ └─────────┘ └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 6.2.1 侧边栏导航

```
┌─────────────────┐
│ 🔥 CodeSeer     │
├─────────────────┤
│ 📌 工作台   ←当前│
│ 📝 需求         │
│ 🔄 迭代         │
│ 📁 项目         │
│ 📊 早会         │
│ 🔧 MCP配置      │
├─────────────────┤
│ ⚙️ 系统设置     │
└─────────────────┘
```

### 6.3 工作台页面

工作台是用户登录后的主入口，展示内容可自定义。

#### 6.3.1 工作台布局

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Logo   │  工作台  │  需求  │  迭代  │  项目  │  早会  │  MCP配置  │ [头像]│
├─────────┴─────────┴────────┴────────┴────────┴────────┴──────────┴──────┤
│                                                                          │
│  ┌─────────────────────────┐ ┌────────────────────────────────────────┐ │
│  │  当前迭代               │ │  快捷操作                                │ │
│  │  v1.0.0 - Sprint 2    ▼ │ │  [早会视图] [切换迭代 ▼]                 │ │
│  └─────────────────────────┘ └────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  我的任务 (3个需求，共8个任务)                                  │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │  需求：用户登录功能                      [进行中] ●●●●○○ 60%    │  │
│  │  任务：实现注册API ✅ | 数据库迁移 ✅ | 登录API 🔄 | 前端 ◌     │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │  需求：订单支付功能                      [进行中] ●●○○○ 40%    │  │
│  │  任务：支付API 🔄 | 微信支付 🔄 | 支付宝 ◌ | 前端 ◌           │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │  需求：商品收藏功能                      [待领取] ○○○○○  0%    │  │
│  │  任务：-                                                        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────┐ ┌──────────────────────────────────────┐│
│  │  📊 迭代概览             │ │  ⚠️ 阻塞提醒 (0)                    ││
│  │  总需求：5               │ │  无阻塞需求                           ││
│  │  已完成：1               │ │                                      ││
│  │  进行中：3               │ │                                      ││
│  │  待领取：1               │ │                                      ││
│  │  进度：60%               │ │                                      ││
│  └──────────────────────────┘ └──────────────────────────────────────┘│
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  📋 待办需求                                      [查看全部]   │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │  商品退款功能      P1   v1.0.0   [待指派]     -                │  │
│  │  用户头像上传      P2   v1.0.0   [已指派]     张三            │  │
│  │  订单导出Excel     P2   v1.1.0   [已指派]     李四            │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 6.3.2 工作台卡片（可自定义）

| 卡片 | 内容 |
|------|------|
| 我的任务 | 当前用户被指派的需求列表，以任务维度展示 |
| 迭代概览 | 总需求数、已完成、进行中、待领取、进度百分比 |
| 阻塞提醒 | 当前有阻塞的需求列表 |
| 今日工作 | 当天需要完成的任务/需求 |
| 待办需求 | 所有待处理的需求列表 |

### 6.4 早会视图页面

展示每个开发的进度和延期情况。

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🔥 CodeSeer  │  工作台  │  需求  │  迭代  │  项目  │  早会  │  MCP配置  │
├───────────────┴──────────┴────────┴────────┴────────┴────────┴──────────┤
│                                                                          │
│  早会视图  │  迭代：v1.0.0 - Sprint 2  ▼  │  日期：2024-06-15  │  [导出]  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  ⚠️ 延期提醒 (2个需求)                           [查看详情]         │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │  🔴 用户登录功能   - 延期1天   原定: 06/14   当前: 06/15   张三    │ │
│  │  🔴 订单支付功能   - 延期2天   原定: 06/13   当前: 06/15   李四    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  👤 张三                    进行中: 2个需求    完成: 1个需求        │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │                                                                      │
│  │  需求：用户登录功能                                    [进行中] 60% │
│  │  ├─ 任务进度：2/4 任务完成                                     │ │
│  │  ├─ 今日完成：实现注册API                                       │ │
│  │  └─ 明日计划：完成登录API                                       │ │
│  │                                                                      │
│  │  需求：商品收藏功能                                    [待领取] 0% │
│  │  ├─ 任务进度：0/3 任务完成                                     │ │
│  │  ├─ 今日完成：-                                                │ │
│  │  └─ 明日计划：领取需求，开始任务拆分                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  👤 李四                    进行中: 1个需求    完成: 0个需求        │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │                                                                      │
│  │  需求：订单支付功能                                    [进行中] 40% │
│  │  ├─ 任务进度：1/4 任务完成                                     │ │
│  │  ├─ 今日完成：支付API开发                                       │ │
│  │  └─ 明日计划：完成微信支付、支付宝支付                         │ │
│  │  └─ ⚠️ 阻塞：第三方支付接口文档未提供                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.5 需求详情页

包含多个 Tab：基本信息、任务、测试记录、文档、活动日志。

#### 6.5.1 需求详情 - 基本信息 Tab

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← 返回工作台                                                           │
│                                                                          │
│  用户登录功能                                           [进行中] ●●●●○○ │
│                                                                          │
│  基本信息    │  任务    │  测试记录  │  文档  │  活动日志                  │
│  ───────────┼─────────┼───────────┼────────┼────────                      │
│ (当前Tab)   │         │           │        │                             │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  基本信息                                                         │  │
│  │                                                                   │  │
│  │  迭代：v1.0.0 - Sprint 2                                          │  │
│  │  优先级：P1                                                        │  │
│  │  指派给：张三                    创建人：产品经理A                  │  │
│  │  截止日期：2024-06-20              创建时间：2024-06-10           │  │
│  │                                                                   │  │
│  │  描述：                                                            │  │
│  │  As a 用户, I want 通过手机号登录, so that 可以快速进入系统       │  │
│  │                                                                   │  │
│  │  验收标准：                                                        │  │
│  │  ☑ 支持中国大陆手机号段                                          │  │
│  │  ☑ 验证码有效期5分钟                                              │  │
│  │  ☐ 登录失败3次后需等待5分钟                                       │  │
│  │                                                                   │  │
│  │  Skill分析结果：                                                    │  │
│  │  ├─ 影响模块：用户中心/认证 (高)                                   │  │
│  │  ├─ 预估工时：8-16小时                                             │  │
│  │  └─ 建议：建议集成现有SMS服务                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 6.5.2 需求详情 - 任务 Tab

```
┌──────────────────────────────────────────────────────────────────────────┐
│  基本信息    │  任务    │  测试记录  │  文档  │  活动日志                  │
├──────────────┼─────────┴───────────┴────────┴───────────────────────────│
│              │ (当前Tab)                                                  │
│                                                                          │
│  开发阶段：需求澄清 ✅ → 任务规划 ✅ → 任务执行 ◐ → 代码审查 ○ → 单元测试 ○│
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  任务列表 (4个)                                    [同步任务]    │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │  #   │ 任务名称         │ 状态     │ TDD进度         │ 完成时间    │ │
│  ├─────┼──────────────────┼──────────┼────────────────┼────────────┤ │
│  │  1  │ 实现用户注册API  │ ✅ 完成  │ ✓→✓→✓         │ 11:00      │ │
│  │  2  │ 编写数据库迁移   │ ✅ 完成  │ ✓→✓→✓         │ 11:30      │ │
│  │  3  │ 实现登录API      │ 🔄 进行中│ ✓→✓→○         │ -          │ │
│  │  4  │ 前端登录页面     │ ○ 待开始 │ -              │ -          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 6.5.3 需求详情 - 测试记录 Tab

```
┌──────────────────────────────────────────────────────────────────────────┐
│  基本信息    │  任务    │  测试记录  │  文档  │  活动日志                  │
├──────────────┴─────────┼───────────┴────────┴───────────────────────────│
│                      │ (当前Tab)                                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  单元测试汇总                                       [提交测试]    │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │  总测试数：70    通过：68    失败：2    覆盖率：87.0%    结果：❌   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  测试记录详情                                                   │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │  任务        │ 类型   │ 总数 │ 通过 │ 失败 │ 覆盖率 │ 结果        │ │
│  ├─────────────┼────────┼──────┼──────┼──────┼────────┼─────────────┤ │
│  │ 实现注册API │ 单元   │  50  │  48  │   2  │ 85.5%  │ ❌ 部分通过 │ │
│  │ 数据库迁移  │ 单元   │  20  │  20  │   0  │ 90.0%  │ ✅ 全部通过 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  失败的测试用例                                                 │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │  test_user_phone_validation (注册API)                             │ │
│  │    └─ 边界条件未处理                                             │ │
│  │  test_duplicate_phone (注册API)                                  │ │
│  │    └─ 未正确返回错误码                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.6 页面路由设计

| 路径 | 页面 |
|------|------|
| `/` | 工作台 |
| `/requirements` | 需求列表 |
| `/requirements/:id` | 需求详情 |
| `/iterations` | 迭代列表 |
| `/iterations/:id` | 迭代详情 |
| `/projects` | 项目列表 |
| `/projects/:id` | 项目详情 |
| `/standup` | 早会视图 |
| `/mcp-config` | MCP 配置 |
| `/settings` | 系统设置 |

---

## 七、待确认事项

1. **需求表无需模块字段**：产品上传需求时不知道涉及哪些模块，模块在分析阶段或文档归档时才确定

2. **文档状态设计**：
   - 草稿状态：开发提交后，尚未正式归档
   - 正式归档：迭代上线后自动转正，Skill 可引用

3. **Skill 生成**：新模块自动生成，老模块动态引用

4. **项目和迭代**：
   - 项目（Project）：一个项目包含多个迭代
   - 迭代（Iteration）= 版本（Version）
   - 需求 → 迭代 → 项目

5. **开发阶段**：
   - 需求澄清 → 任务规划 → 任务执行（TDD循环）→ 代码审查 → 单元测试
   - 任务拆分由 Superpower 决定，平台负责记录和展示
   - MCP 自动同步任务列表和测试结果

---

## 八、后续工作

1. 确认设计方案
2. 编写详细实现计划
3. 开始核心模块开发