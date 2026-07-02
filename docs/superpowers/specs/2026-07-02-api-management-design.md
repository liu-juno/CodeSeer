# API 管理模块设计方案

> **目标**：API 变更追踪 + 在线测试 + 与需求流程深度集成

## 1. 核心场景

### 场景 A：开发阶段（OpenCode 驱动）
1. OpenCode 开发某个需求时，识别到代码涉及了哪些 API 端点
2. 实时上报接口变更（新增 / 修改 / 删除）到平台
3. 平台记录变更，标记该 API 状态为 "待文档更新"
4. 开发者可在平台上更新接口文档
5. 接口文档变更后，标记为 "待测试"

### 场景 B：测试阶段
1. 测试人员进入迭代 → 查看该迭代关联的 API 变更列表
2. 对每个变更接口执行在线测试（填参数 → 发送 → 记录结果）
3. 测试通过 → 接口状态变为 "已测试"
4. 测试不通过 → 记录失败原因，可指派给开发者修复

---

## 2. 数据模型

### 2.1 ApiEndpoint（接口定义）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | UUID |
| project_id | string | FK → projects |
| module_id | string | FK → modules（可选） |
| method | string | GET/POST/PUT/DELETE/PATCH |
| path | string | /api/v1/users |
| summary | string | 接口描述 |
| description | text | 详细说明 |
| request_schema | text | 请求参数 JSON Schema（JSON 存储） |
| response_schema | text | 响应参数 JSON Schema（JSON 存储） |
| headers | text | 公共 Header 配置（JSON） |
| status | enum | draft / published / deprecated |
| version | int | 当前版本号 |
| created_by | string | |
| created_at | datetime | |
| updated_at | datetime | |

### 2.2 ApiEndpointVersion（接口版本历史）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | |
| endpoint_id | string | FK → api_endpoints |
| version | int | 版本号 |
| request_schema | text | 该版本的请求 schema |
| response_schema | text | 该版本的响应 schema |
| change_note | string | 变更说明 |
| created_by | string | |
| created_at | datetime | |

### 2.3 ApiRequirementMapping（接口-需求关联）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | |
| endpoint_id | string | FK → api_endpoints |
| requirement_id | string | FK → requirements |
| change_type | enum | created / modified / deleted |
| change_note | string | 变更描述 |
| reported_at | datetime | 上报时间 |
| reported_by | string | OpenCode 上报 |

### 2.4 ApiEnvironment（测试环境）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | |
| project_id | string | FK → projects |
| name | string | 开发环境 / 测试环境 / 生产环境 |
| base_url | string | https://api-dev.example.com |
| variables | text | 环境变量 JSON，如 { "token": "xxx" } |
| is_default | bool | 是否默认环境 |

### 2.5 ApiTestCase（测试用例）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | |
| endpoint_id | string | FK → api_endpoints |
| name | string | 用例名称，如 "正常创建用户" |
| request_params | text | 请求参数 JSON |
| expected_status | int | 期望响应码 |
| expected_response | text | 期望响应内容（JSON，可选） |
| created_by | string | |
| created_at | datetime | |

### 2.6 ApiTestRecord（测试记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | |
| endpoint_id | string | FK → api_endpoints |
| test_case_id | string | FK → api_test_cases（可选） |
| requirement_id | string | FK → requirements（关联的需求） |
| environment_id | string | FK → api_environments |
| request_params | text | 本次请求参数 |
| response_status | int | 实际响应码 |
| response_body | text | 实际响应内容 |
| response_time | int | 响应时间 ms |
| result | enum | pass / fail / error |
| error_message | text | 失败原因 |
| executed_by | string | |
| executed_at | datetime | |

---

## 3. MCP 上报接口（OpenCode → 平台）

新增 MCP tool：

```json
{
  "name": "report_api_changes",
  "description": "上报代码变更涉及的 API 接口",
  "inputSchema": {
    "type": "object",
    "properties": {
      "requirement_id": { "type": "string" },
      "changes": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "method": { "type": "string" },
            "path": { "type": "string" },
            "change_type": { "type": "string", "enum": ["created", "modified", "deleted"] },
            "summary": { "type": "string" },
            "change_note": { "type": "string" }
          },
          "required": ["method", "path", "change_type"]
        }
      }
    },
    "required": ["requirement_id", "changes"]
  }
}
```

---

## 4. 功能模块

### 4.1 接口列表
- 按项目展示所有接口
- 筛选：方法、模块、状态
- 搜索：path / summary
- 支持手动新增接口（填 method、path、schema）

### 4.2 接口详情
- 基本信息（method、path、描述）
- 请求/响应 Schema（JSON 编辑器）
- 版本历史
- 关联的需求列表（带变更类型标签）
- 关联的文档
- 在线测试入口

### 4.3 接口变更记录
- 按迭代查看变更列表
- 变更类型标签（created/modified/deleted）
- 上报时间 + 上报者
- 一键跳转测试

### 4.4 在线测试
- 选择环境（切换 base_url + 变量）
- 选择接口 → 加载 Schema → 填参数
- 发送请求 → 显示响应（状态码、耗时、body）
- 保存为测试用例
- 执行测试用例 → 记录结果

### 4.5 测试记录
- 按接口 / 按迭代 / 按时间查看测试历史
- 通过/失败状态统计
- 失败详情（对比期望响应）

---

## 5. 暂不实现（后续迭代）

- [ ] Mock 服务
- [ ] Swagger/OpenAPI 导入
- [ ] 接口依赖分析
- [ ] 自动化测试（CI 集成）

---

## 6. 实现顺序

**Phase 1：基础 CRUD + 版本管理**
- ApiEndpoint 数据模型
- 接口列表 + 详情
- 版本历史

**Phase 2：在线测试**
- 环境管理
- 测试执行
- 测试记录

**Phase 3：需求关联 + MCP 上报**
- ApiRequirementMapping
- MCP tool report_api_changes
- 接口变更列表

**Phase 4：测试用例**
- 测试用例管理
- 用例执行 → 记录
