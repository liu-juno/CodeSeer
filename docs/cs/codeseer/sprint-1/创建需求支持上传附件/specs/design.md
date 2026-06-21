# 设计文档：创建需求支持上传附件

## 1. 背景

作为产品经理，在创建需求时需要上传附件（如需求文档、截图等），以便 AIAgent 能获取更丰富的信息来理解需求。

AIAgent 在拉取开发需求时，需要同时获取需求及对应的附件，以便更好地理解需求内容。

## 2. 架构设计

### 2.1 技术选型

- **存储后端**：本地文件系统（`/tmp/codeforge/attachments/`）
- **数据库**：SQLite（现有）
- **文件大小限制**：100MB

### 2.2 数据库模型

新建 `RequirementAttachment` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | 主键 UUID |
| requirement_id | String(36) | 外键关联 Requirement |
| filename | String(255) | 原始文件名 |
| file_size | Integer | 文件大小（字节） |
| content_type | String(100) | MIME 类型 |
| storage_path | String(500) | 存储路径 |
| storage_backend | String(20) | 存储后端：local |
| created_at | DateTime | 上传时间 |

## 3. API 设计

### 3.1 上传附件

```
POST /requirements/{requirement_id}/attachments
Content-Type: multipart/form-data

Body:
  - file: 二进制文件

Response 201:
{
  "id": "uuid",
  "filename": "需求文档.pdf",
  "file_size": 102400,
  "content_type": "application/pdf"
}
```

### 3.2 列出附件

```
GET /requirements/{requirement_id}/attachments

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "filename": "需求文档.pdf",
      "file_size": 102400,
      "content_type": "application/pdf",
      "created_at": "2026-06-21T10:00:00Z"
    }
  ]
}
```

### 3.3 下载附件

```
GET /requirements/{requirement_id}/attachments/{attachment_id}/download

Response 200:
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="需求文档.pdf"
  [二进制文件内容]
```

### 3.4 删除附件

```
DELETE /requirements/{requirement_id}/attachments/{attachment_id}

Response 200:
{
  "message": "附件已删除"
}
```

## 4. AIAgent 集成

### 4.1 扩展 `get_requirement` 响应

在现有 `get_requirement` 响应中增加 `attachments` 字段：

```json
{
  "id": "xxx",
  "title": "需求标题",
  "description": "...",
  "attachments": [
    {
      "id": "aid",
      "filename": "需求文档.pdf",
      "file_size": 102400,
      "content_type": "application/pdf"
    }
  ]
}
```

### 4.2 新增 `download_attachment` MCP 工具

```
工具名：download_attachment
输入：requirement_id, attachment_id
输出：二进制文件内容（base64 编码）
```

### 4.3 AIAgent 调用流程

1. AIAgent 调用 `get_requirement` → 获取附件列表
2. AIAgent 调用 `download_attachment(requirement_id, attachment_id)` → 获取附件内容
3. AIAgent 基于附件内容更好地理解需求

## 5. 前端设计

### 5.1 创建需求页面

- 文件选择器（支持多选）
- 上传进度条
- 已上传附件列表（可预览/删除）
- 附件与需求一并提交

## 6. 存储路径

```
/tmp/codeforge/attachments/{requirement_id}/{uuid}_{original_filename}
```

## 7. 约束

- 单个文件大小限制：100MB
- 支持的文件类型：任意（不限制 MIME 类型）
- 存储后端：local（后续可扩展 OSS/FTP）
