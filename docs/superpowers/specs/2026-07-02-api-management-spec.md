# API 管理模块需求规格

> **场景**：团队在 CodeSeer 平台管理项目接口，支持手动录入、在线测试、测试用例管理，与 OpenCode 的变更上报暂在后续迭代实现。

---

## 1. 核心功能

### 1.1 接口管理
- **接口列表**：按项目展示，支持筛选（method、模块、状态）和搜索（path / summary）
- **接口详情**：基本信息 + 请求/响应 Schema（JSON）+ 版本历史
- **接口 CRUD**：新增、编辑、删除接口
- **版本历史**：每次变更记录版本号、Schema Diff、变更说明

### 1.2 环境管理
- 每个项目支持多个测试环境（如：开发环境、测试环境、生产环境）
- 每个环境配置：名称、base_url、公共 Header 变量
- 支持设置默认环境

### 1.3 在线测试
- 选择接口 → 选择环境 → 填写参数 → 发送请求
- 查看响应：状态码、响应时间、响应内容
- 测试结果自动记录到测试记录

### 1.4 测试用例管理
- 为接口维护测试用例（预设参数 + 期望响应码）
- 支持执行用例并对比期望结果
- 用例结果记录到测试记录

### 1.5 测试记录
- 按接口 / 环境 / 时间查看历史测试记录
- 记录通过/失败状态
- 失败时显示期望值 vs 实际值

---

## 2. 数据模型

### api_endpoints（接口定义）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | PK |
| project_id | String(36) | FK → projects |
| module_id | String(36) | FK → modules（可选） |
| method | String(10) | GET/POST/PUT/DELETE/PATCH |
| path | String(200) | /api/v1/users |
| summary | String(200) | 接口描述 |
| description | Text | 详细说明 |
| request_schema | Text | 请求参数 JSON Schema |
| response_schema | Text | 响应参数 JSON Schema |
| headers | Text | 公共 Header（JSON） |
| status | Enum | draft / published / deprecated |
| version | Integer | 当前版本号 |
| created_by | String(36) | |
| created_at | DateTime | |
| updated_at | DateTime | |

### api_endpoint_versions（接口版本）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | PK |
| endpoint_id | String(36) | FK → api_endpoints |
| version | Integer | 版本号 |
| request_schema | Text | 该版本请求 Schema |
| response_schema | Text | 该版本响应 Schema |
| change_note | String(500) | 变更说明 |
| created_by | String(36) | |
| created_at | DateTime | |

### api_environments（测试环境）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | PK |
| project_id | String(36) | FK → projects |
| name | String(50) | 开发环境 / 测试环境 |
| base_url | String(200) | https://api-dev.example.com |
| variables | Text | 环境变量（JSON） |
| is_default | Boolean | 是否默认环境 |
| created_at | DateTime | |
| updated_at | DateTime | |

### api_test_cases（测试用例）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | PK |
| endpoint_id | String(36) | FK → api_endpoints |
| name | String(200) | 用例名称 |
| request_params | Text | 请求参数（JSON） |
| expected_status | Integer | 期望响应码 |
| expected_response | Text | 期望响应内容（JSON，可选） |
| created_by | String(36) | |
| created_at | DateTime | |

### api_test_records（测试记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | PK |
| endpoint_id | String(36) | FK → api_endpoints |
| test_case_id | String(36) | FK → api_test_cases（可选） |
| environment_id | String(36) | FK → api_environments |
| request_params | Text | 本次请求参数 |
| response_status | Integer | 实际响应码 |
| response_body | Text | 实际响应内容 |
| response_time_ms | Integer | 响应时间 ms |
| result | Enum | pass / fail / error |
| error_message | Text | 失败原因 |
| executed_by | String(36) | |
| executed_at | DateTime | |

---

## 3. 后端 API 接口

### 环境管理
- `GET /api/projects/{project_id}/environments` - 获取项目所有环境
- `POST /api/projects/{project_id}/environments` - 创建环境
- `PUT /api/environments/{id}` - 更新环境
- `DELETE /api/environments/{id}` - 删除环境

### 接口管理
- `GET /api/projects/{project_id}/endpoints` - 获取项目所有接口
- `GET /api/endpoints/{id}` - 获取接口详情
- `POST /api/projects/{project_id}/endpoints` - 创建接口
- `PUT /api/endpoints/{id}` - 更新接口
- `DELETE /api/endpoints/{id}` - 删除接口
- `GET /api/endpoints/{id}/versions` - 获取版本历史

### 测试
- `POST /api/endpoints/{id}/test` - 在线测试（执行请求，返回响应）
- `GET /api/endpoints/{id}/test-cases` - 获取测试用例
- `POST /api/endpoints/{id}/test-cases` - 创建测试用例
- `PUT /api/test-cases/{id}` - 更新测试用例
- `DELETE /api/test-cases/{id}` - 删除测试用例
- `POST /api/test-cases/{id}/run` - 执行测试用例
- `GET /api/endpoints/{id}/test-records` - 获取测试记录

---

## 4. 暂不实现（后续迭代）

- [ ] Mock 服务
- [ ] Swagger/OpenAPI 导入
- [ ] OpenCode 接口变更上报（report_api_changes MCP tool）
- [ ] OpenCode 测试结果上报（report_api_test_results MCP tool）
- [ ] 接口需求关联追踪
- [ ] 迭代变更接口列表

---

## 5. 实现顺序

### Phase 1：接口 CRUD + 版本历史
1. 数据模型 + Schema
2. 接口列表 + 详情页
3. 接口新增/编辑（含 JSON Schema 编辑器）
4. 版本历史展示

### Phase 2：环境管理
1. 环境 CRUD
2. 环境选择器组件

### Phase 3：在线测试
1. 测试执行 API（实际发 HTTP 请求）
2. 测试页面（选接口 → 选环境 → 填参数 → 发请求 → 展示响应）

### Phase 4：测试用例 + 记录
1. 测试用例 CRUD
2. 执行用例 → 对比期望值
3. 测试记录列表
