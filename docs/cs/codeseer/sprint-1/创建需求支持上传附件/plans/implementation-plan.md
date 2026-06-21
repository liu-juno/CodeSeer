# 创建需求支持上传附件 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在创建需求时支持上传附件，AIAgent 能获取附件内容

**Architecture:** 附件存储在本地文件系统 `/tmp/codeforge/attachments/`，元数据存 SQLite 独立表 `requirement_attachments`。MCP 工具扩展 `get_requirement` 返回附件列表，新增 `download_attachment` 工具获取附件内容。

**Tech Stack:** FastAPI (Python), SQLAlchemy, Vue 3 + Element Plus, SQLite

## Global Constraints

- 文件大小限制：100MB
- 存储路径：`/tmp/codeforge/attachments/{requirement_id}/{uuid}_{filename}`
- AIAgent 集成：扩展现有 `get_requirement` + 新增 `download_attachment` MCP 工具

---

## Task 1: 创建 RequirementAttachment 模型

**Files:**
- Modify: `backend/app/models/models.py` — 添加 `RequirementAttachment` model

**Interfaces:**
- Produces: `RequirementAttachment` model class

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_attachments.py
import pytest
from app.models.models import RequirementAttachment

def test_requirement_attachment_model_exists():
    assert hasattr(RequirementAttachment, '__tablename__')
    assert RequirementAttachment.__tablename__ == 'requirement_attachments'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && python -m pytest tests/test_attachments.py::test_requirement_attachment_model_exists -v`
Expected: FAIL — `RequirementAttachment` not found

- [ ] **Step 3: Add RequirementAttachment model to models.py**

在 `backend/app/models/models.py` 文件末尾添加：

```python
class RequirementAttachment(Base):
    __tablename__ = "requirement_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=True)
    storage_path = Column(String(500), nullable=False)
    storage_backend = Column(String(20), default="local")
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("Requirement", backref="attachments")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && python -m pytest tests/test_attachments.py::test_requirement_attachment_model_exists -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/models.py backend/tests/test_attachments.py
git commit -m "feat: add RequirementAttachment model for requirement file uploads"
```

---

## Task 2: 实现附件 API 端点

**Files:**
- Create: `backend/app/api/attachments.py` — 附件上传/下载/删除/列表 API
- Modify: `backend/app/main.py` — 注册 attachments router

**Interfaces:**
- Consumes: `RequirementAttachment` model from Task 1
- Produces: `/requirements/{id}/attachments` CRUD endpoints

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_attachments.py
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_list_attachments_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/requirements/test-id/attachments")
    assert resp.status_code == 404  # requirement not found
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && python -m pytest tests/test_attachments.py::test_list_attachments_empty -v`
Expected: FAIL — endpoint not found (404)

- [ ] **Step 3: Create attachments API router**

创建 `backend/app/api/attachments.py`：

```python
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.models import Requirement, RequirementAttachment

router = APIRouter(prefix="/requirements", tags=["attachments"])

BASE_DIR = "/tmp/codeforge/attachments"
os.makedirs(BASE_DIR, exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    content_type: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{requirement_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    requirement_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # verify requirement exists
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Requirement not found")

    # save file
    file_id = str(uuid.uuid4())
    safe_filename = file.filename or "unknown"
    storage_path = os.path.join(BASE_DIR, requirement_id, f"{file_id}_{safe_filename}")
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 100MB)")

    async with open(storage_path, 'wb') as f:
        await f.write(content)

    # save to db
    attachment = RequirementAttachment(
        id=file_id,
        requirement_id=requirement_id,
        filename=safe_filename,
        file_size=len(content),
        content_type=file.content_type,
        storage_path=storage_path,
        storage_backend="local",
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.get("/{requirement_id}/attachments", response_model=List[AttachmentResponse])
async def list_attachments(requirement_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequirementAttachment)
        .where(RequirementAttachment.requirement_id == requirement_id)
        .order_by(RequirementAttachment.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{requirement_id}/attachments/{attachment_id}/download")
async def download_attachment(
    requirement_id: str,
    attachment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RequirementAttachment)
        .where(
            RequirementAttachment.id == attachment_id,
            RequirementAttachment.requirement_id == requirement_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.storage_path):
        raise HTTPException(status_code=404, detail="File not found on storage")

    async with open(attachment.storage_path, 'rb') as f:
        content = await f.read()

    return Response(
        content=content,
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=\"{attachment.filename}\""},
    )


@router.delete("/{requirement_id}/attachments/{attachment_id}")
async def delete_attachment(requirement_id: str, attachment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequirementAttachment)
        .where(
            RequirementAttachment.id == attachment_id,
            RequirementAttachment.requirement_id == requirement_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if os.path.exists(attachment.storage_path):
        os.remove(attachment.storage_path)

    await db.delete(attachment)
    await db.commit()
    return {"message": "Attachment deleted"}
```

- [ ] **Step 4: Register router in main.py**

在 `backend/app/main.py` 添加：

```python
from app.api.attachments import router as attachments_router
app.include_router(attachments_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && python -m pytest tests/test_attachments.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/attachments.py backend/app/main.py backend/tests/test_attachments.py
git commit -m "feat: add attachment upload/download/delete/list API endpoints"
```

---

## Task 3: 前端附件 API 客户端

**Files:**
- Modify: `frontend/src/api/index.ts` — 添加 `attachmentsApi`

**Interfaces:**
- Consumes: Backend attachment API endpoints from Task 2
- Produces: `attachmentsApi` object with upload/list/download/delete methods

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/tests/attachments.test.ts
import { attachmentsApi } from '@/api'

describe('attachmentsApi', () => {
  it('should have upload method', () => {
    expect(typeof attachmentsApi.upload).toBe('function')
  })
  it('should have list method', () => {
    expect(typeof attachmentsApi.list).toBe('function')
  })
  it('should have download method', () => {
    expect(typeof attachmentsApi.download).toBe('function')
  })
  it('should have delete method', () => {
    expect(typeof attachmentsApi.delete).toBe('function')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/frontend && npm test -- --run tests/attachments.test.ts`
Expected: FAIL — `attachmentsApi` not found

- [ ] **Step 3: Add attachmentsApi to frontend/src/api/index.ts**

在 `frontend/src/api/index.ts` 末尾添加：

```typescript
// Attachments API
export const attachmentsApi = {
  upload: (requirementId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/requirements/${requirementId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: (requirementId: string) =>
    api.get(`/requirements/${requirementId}/attachments`),
  download: (requirementId: string, attachmentId: string) =>
    api.get(`/requirements/${requirementId}/attachments/${attachmentId}/download`, {
      responseType: 'blob',
    }),
  delete: (requirementId: string, attachmentId: string) =>
    api.delete(`/requirements/${requirementId}/attachments/${attachmentId}`),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/frontend && npm test -- --run tests/attachments.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/tests/attachments.test.ts
git commit -m "feat: add attachmentsApi to frontend"
```

---

## Task 4: 扩展 AIAgent MCP 工具 — get_requirement 返回附件

**Files:**
- Modify: `backend/app/api/mcp_handlers.py` — 扩展 `_get_requirement_detail` 返回 attachments

**Interfaces:**
- Consumes: `RequirementAttachment` model
- Produces: `get_requirement_detail` MCP tool returns `attachments` array

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_mcp_attachments.py
@pytest.mark.asyncio
async def test_get_requirement_returns_attachments(async_client, db_session):
    # Create requirement and attachment
    # Call _get_requirement_detail
    # Assert attachments in response
    pass
```

- [ ] **Step 2: Implement — query attachments in _get_requirement_detail**

修改 `_get_requirement_detail` 函数，添加附件查询：

```python
async def _get_requirement_detail(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    if not req_id:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        return {"__not_found__": True}
    tasks_result = await db.execute(
        select(Task).where(Task.requirement_id == req_id).order_by(Task.order)
    )
    tasks = tasks_result.scalars().all()

    # Query attachments
    attachments_result = await db.execute(
        select(RequirementAttachment)
        .where(RequirementAttachment.requirement_id == req_id)
        .order_by(RequirementAttachment.created_at.desc())
    )
    attachments = attachments_result.scalars().all()

    status = req.status.value if hasattr(req.status, "value") else req.status
    priority = req.priority.value if hasattr(req.priority, "value") else req.priority
    task_lines = "\n".join(
        f"  {i+1}. [{t.status.value if hasattr(t.status, 'value') else t.status}] {t.title}"
        for i, t in enumerate(tasks)
    ) or "  （暂无任务）"

    attachment_lines = "\n".join(
        f"  - {a.filename} (id={a.id}, size={a.file_size})"
        for a in attachments
    ) or "  （暂无附件）"

    text = (
        f"需求详情\n"
        f"标题: {req.title}\n"
        f"状态: {status}\n"
        f"优先级: {priority}\n"
        f"描述: {req.description or '无'}\n"
        f"验收标准: {req.acceptance_criteria or '无'}\n"
        f"附件列表:\n{attachment_lines}\n"
        f"任务列表:\n{task_lines}"
    )
    return _text(text)
```

- [ ] **Step 3: Run existing MCP tests to verify no regression**

Run: `cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && python -m pytest tests/test_mcp_tools_call.py -v`

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/mcp_handlers.py
git commit -m "feat(mcp): get_requirement returns attachments list"
```

---

## Task 5: 新增 download_attachment MCP 工具

**Files:**
- Modify: `backend/app/api/mcp_tools.py` — 添加 `download_attachment` tool
- Modify: `backend/app/api/mcp_handlers.py` — 添加 `_download_attachment` handler
- Modify: `backend/app/api/mcp_http.py` — 注册新工具到 MCP HTTP 接口

**Interfaces:**
- Consumes: `RequirementAttachment` model
- Produces: `download_attachment` MCP tool that returns base64-encoded file content

- [ ] **Step 1: Add tool definition to mcp_tools.py**

在 `TOOLS` 数组末尾添加：

```python
{
    "name": "download_attachment",
    "description": "下载需求的附件内容（返回 base64 编码）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "requirement_id": {"type": "string", "description": "需求 ID"},
            "attachment_id": {"type": "string", "description": "附件 ID"},
        },
        "required": ["requirement_id", "attachment_id"],
    },
},
```

- [ ] **Step 2: Add handler in mcp_handlers.py**

```python
async def _download_attachment(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    attachment_id = args.get("attachment_id")
    if not req_id or not attachment_id:
        return None

    result = await db.execute(
        select(RequirementAttachment).where(
            RequirementAttachment.id == attachment_id,
            RequirementAttachment.requirement_id == req_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        return {"__not_found__": True}

    if not os.path.exists(attachment.storage_path):
        return _text(f"文件不存在：{attachment.filename}")

    import base64
    with open(attachment.storage_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')

    return _text(
        f"附件内容（base64）：\n"
        f"文件名：{attachment.filename}\n"
        f"大小：{attachment.file_size} 字节\n"
        f"类型：{attachment.content_type}\n\n"
        f"```\n{content}\n```"
    )
```

- [ ] **Step 3: Register handler in TOOL_HANDLERS**

```python
TOOL_HANDLERS = {
    # ... existing handlers ...
    "download_attachment": _download_attachment,
}
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/mcp_tools.py backend/app/api/mcp_handlers.py
git commit -m "feat(mcp): add download_attachment tool for AIAgent"
```

---

## Task 6: 前端 — 创建需求页面添加附件上传

**Files:**
- Modify: `frontend/src/views/Requirements.vue` — 在 wizard 第 2 步添加附件上传

**Interfaces:**
- Consumes: `attachmentsApi` from Task 3
- Produces: File upload UI in requirement creation wizard

- [ ] **Step 1: Add failing test**

```typescript
// frontend/src/tests/Requirements.attachments.test.ts
import { mount } from '@vue/test-utils'
import Requirements from '@/views/Requirements.vue'

it('wizard step 2 should show file upload', async () => {
  // mount and check for el-upload component
})
```

- [ ] **Step 2: Implement file upload in wizard**

在 `Requirements.vue` 的 step 2 (`currentStep === 1`) 中添加：

```vue
<div v-show="currentStep === 1">
  <el-form-item label="需求描述">
    <el-input v-model="form.description" type="textarea" :rows="8" />
  </el-form-item>
  <el-form-item label="附件上传">
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :limit="5"
      :on-change="onFileChange"
      :on-remove="onFileRemove"
      multiple
    >
      <el-button type="primary" plain>选择文件</el-button>
      <template #tip>
        <div class="el-upload__tip">最多上传 5 个文件，单个文件不超过 100MB</div>
      </template>
    </el-upload>
    <div v-if="uploadedFiles.length" style="margin-top:12px;">
      <div v-for="(f, i) in uploadedFiles" :key="i" style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
        <el-icon><Document /></el-icon>
        <span style="flex:1; font-size:13px;">{{ f.name }}</span>
        <span style="color:#909399; font-size:12px;">{{ (f.size / 1024).toFixed(1) }} KB</span>
        <el-button text type="danger" size="small" @click="removeFile(i)">×</el-button>
      </div>
    </div>
  </el-form-item>
  <!-- criteria remains unchanged below -->
</div>
```

添加 `uploadedFiles` 到 `form`：

```typescript
const defaultForm = () => ({
  title: '',
  project_id: '',
  iteration_id: '',
  description: DESCRIPTION_TEMPLATE,
  criteriaList: [''],
  priority: 'P2',
  due_date: '',
  uploadedFiles: [] as File[],
})
```

添加 `onFileChange`, `removeFile` 等方法：

```typescript
const uploadRef = ref()
const onFileChange = (file: any) => {
  form.value.uploadedFiles.push(file.raw)
}
const removeFile = (index: number) => {
  form.value.uploadedFiles.splice(index, 1)
}
```

- [ ] **Step 3: Modify submitRequirement to upload files after requirement creation**

```typescript
const submitRequirement = async () => {
  submitting.value = true
  try {
    const criteria = form.value.criteriaList.filter(c => c.trim()).join('\n')
    const res = await requirementsApi.create({
      title: form.value.title,
      project_id: form.value.project_id,
      iteration_id: form.value.iteration_id || null,
      description: form.value.description,
      acceptance_criteria: criteria,
      priority: form.value.priority,
      due_date: form.value.due_date ? form.value.due_date + 'T00:00:00' : null,
    })
    const requirementId = res.data.id

    // upload attachments
    for (const file of form.value.uploadedFiles) {
      await attachmentsApi.upload(requirementId, file)
    }

    showWizard.value = false
    ElMessage.success('创建成功')
    fetchPage(page.value)
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}
```

- [ ] **Step 4: Add import for Document icon**

```typescript
import { Plus, Document } from '@element-plus/icons-vue'
```

- [ ] **Step 5: Run and verify**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/Requirements.vue
git commit -m "feat(frontend): add file upload to requirement creation wizard"
```

---

## Task 7: 前端 — 需求详情页显示附件

**Files:**
- Modify: `frontend/src/views/RequirementDetail.vue` — 添加"附件"tab 页

**Interfaces:**
- Consumes: `attachmentsApi.list()` and `attachmentsApi.download()`
- Produces: Attachment tab showing list and download buttons

- [ ] **Step 1: Add failing test**

- [ ] **Step 2: Add attachments tab**

在 `RequirementDetail.vue` 的 `<el-tabs>` 中添加新 tab：

```vue
<el-tab-pane name="attachments">
  <template #label>
    附件 <el-badge :value="attachments.length" :hidden="!attachments.length" />
  </template>
  <el-card shadow="never">
    <div v-if="attachments.length === 0" class="ai-placeholder">
      <div class="ai-icon">📎</div>
      <div class="ai-title">暂无附件</div>
      <div class="ai-desc">创建需求时上传的附件将在此处展示</div>
    </div>
    <el-table v-else :data="attachments" stripe>
      <el-table-column prop="filename" label="文件名" min-width="200" />
      <el-table-column prop="file_size" label="大小" width="100">
        <template #default="{ row }">
          {{ (row.file_size / 1024).toFixed(1) }} KB
        </template>
      </el-table-column>
      <el-table-column prop="content_type" label="类型" width="120" />
      <el-table-column prop="created_at" label="上传时间" width="120">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" align="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="downloadAtt(row)">
            下载
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</el-tab-pane>
```

- [ ] **Step 3: Add reactive state and fetch logic**

```typescript
const attachments = ref<any[]>([])

const fetchAttachments = async () => {
  try {
    const res = await attachmentsApi.list(route.params.id as string)
    attachments.value = res.data
  } catch (e) { console.error(e) }
}

const downloadAtt = async (att: any) => {
  try {
    const res = await attachmentsApi.download(route.params.id as string, att.id)
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = att.filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载失败')
    console.error(e)
  }
}

// In onMounted:
fetchAttachments()
```

- [ ] **Step 4: Import attachmentsApi**

```typescript
import { requirementsApi, iterationsApi, tasksApi, testRecordsApi, documentsApi, modulesApi, usersApi, attachmentsApi } from '@/api'
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/RequirementDetail.vue
git commit -m "feat(frontend): show attachments tab in requirement detail"
```

---

## Task 8: 集成测试

**Files:**
- Create: `backend/tests/test_attachments_integration.py` — 完整流程测试

- [ ] **Step 1: Write integration test**

```python
@pytest.mark.asyncio
async def test_full_attachment_flow(async_client, db_session):
    """创建需求 → 上传附件 → 列出附件 → 下载附件 → 删除附件"""
    # 1. Create requirement
    # 2. Upload attachment
    # 3. List attachments
    # 4. Download attachment (verify content matches)
    # 5. Delete attachment
    pass
```

- [ ] **Step 2: Run integration test**

- [ ] **Step 3: Commit**

---

## 实施顺序

1. **Task 1** — RequirementAttachment 模型（基础）
2. **Task 2** — Attachment API 端点（基础）
3. **Task 3** — Frontend API client（前端依赖 Task 2）
4. **Task 4** — MCP get_requirement 扩展附件（Task 1 后可做）
5. **Task 5** — MCP download_attachment 工具（Task 2 后可做）
6. **Task 6** — 创建需求页面上传 UI（Task 3 后可做）
7. **Task 7** — 需求详情展示附件（Task 3 后可做）
8. **Task 8** — 集成测试
