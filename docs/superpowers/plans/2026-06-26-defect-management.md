# 缺陷管理功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 实现独立的缺陷管理模块，支持创建、列表、看板、详情、评论功能

**架构：** 前后端分离，后端 FastAPI + SQLAlchemy，前端 Vue3 + Element Plus。缺陷独立于需求管理，有自己的路由和页面。

**技术栈：** FastAPI, Vue3, Element Plus, Pinia

---

## 全局约束

- 状态：新建 → 待确认 → 修复中 → 待验证 → 已关闭
- 严重程度：致命 / 严重 / 一般 / 轻微
- 优先级：P0 / P1 / P2 / P3
- 创建缺陷时必须指定负责人（可多人）
- 自由流转状态，但记录完整变更日志

---

## 文件结构

```
backend/
├── app/models/models.py          # 新增 DefectSeverity, DefectPriority, DefectStatus, Defect, DefectComment, DefectLog
├── app/schemas/schemas.py        # 新增 Defect* schemas
├── app/api/defects.py            # 新增缺陷 CRUD API
├── app/api/__init__.py           # 注册 defects router
├── app/main.py                   # 注册 defects router

frontend/src/
├── api/index.ts                  # 新增 defectsApi
├── router/index.ts               # 新增 /defects, /defect/new, /defect/:id 路由
├── stores/                       # 新增 defects.ts store
├── views/
│   ├── Defects.vue               # 列表页（表格 + 看板）
│   ├── DefectDetail.vue          # 详情页
│   └── DefectCreate.vue          # 创建页
```

---

## Task 1: 后端 - 添加枚举和 Defect 模型

**Files:**
- Modify: `backend/app/models/models.py` (末尾添加)

**Interfaces:**
- Consumes: 无
- Produces: DefectStatus, DefectSeverity, DefectPriority, Defect, DefectComment, DefectLog 模型

- [ ] **Step 1: 添加枚举和模型**

在 `backend/app/models/models.py` 末尾添加：

```python
class DefectStatus(str, enum.Enum):
    NEW = "new"               # 新建
    CONFIRMED = "confirmed"   # 待确认
    FIXING = "fixing"         # 修复中
    VERIFYING = "verifying"   # 待验证
    CLOSED = "closed"         # 已关闭


class DefectSeverity(str, enum.Enum):
    FATAL = "fatal"     # 致命
    CRITICAL = "critical"  # 严重
    MAJOR = "major"        # 一般
    MINOR = "minor"        # 轻微


class DefectPriority(str, enum.Enum):
    P0 = "p0"   # 紧急
    P1 = "p1"   # 重要
    P2 = "p2"   # 一般
    P3 = "p3"   # 低


class Defect(Base):
    __tablename__ = "defects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)  # Markdown
    severity = Column(Enum(DefectSeverity), default=DefectSeverity.MAJOR)
    priority = Column(Enum(DefectPriority), default=DefectPriority.P2)
    status = Column(Enum(DefectStatus), default=DefectStatus.NEW)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=True)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    iteration_id = Column(String(36), ForeignKey("iterations.id"), nullable=True)
    assignees = Column(Text, nullable=True)  # JSON array of user IDs
    labels = Column(Text, nullable=True)  # JSON array of label strings
    steps_to_reproduce = Column(Text, nullable=True)
    environment = Column(Text, nullable=True)
    creator_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    requirement = relationship("Requirement")
    module = relationship("Module")
    iteration = relationship("Iteration")
    comments = relationship("DefectComment", back_populates="defect", cascade="all, delete-orphan")
    logs = relationship("DefectLog", back_populates="defect", cascade="all, delete-orphan")


class DefectComment(Base):
    __tablename__ = "defect_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    defect_id = Column(String(36), ForeignKey("defects.id"), nullable=False)
    user_id = Column(String(36), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    defect = relationship("Defect", back_populates="comments")


class DefectLog(Base):
    __tablename__ = "defect_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    defect_id = Column(String(36), ForeignKey("defects.id"), nullable=False)
    user_id = Column(String(36), nullable=True)
    action = Column(String(50), nullable=False)  # created, status_changed, updated, commented
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    defect = relationship("Defect", back_populates="logs")
```

- [ ] **Step 2: 运行测试验证**

```bash
cd backend && python -c "from app.models.models import Defect, DefectStatus, DefectSeverity, DefectPriority, DefectComment, DefectLog; print('OK')"
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/models.py
git commit -m "feat: add Defect model and enums"
```

---

## Task 2: 后端 - 添加 Defect schemas

**Files:**
- Modify: `backend/app/schemas/schemas.py` (末尾添加)

**Interfaces:**
- Consumes: Defect, DefectComment, DefectLog 模型
- Produces: DefectCreate, DefectUpdate, DefectResponse, DefectCommentCreate, DefectLogResponse schemas

- [ ] **Step 1: 添加 schemas**

在 `backend/app/schemas/schemas.py` 末尾添加：

```python
class DefectBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: DefectSeverity = DefectSeverity.MAJOR
    priority: DefectPriority = DefectPriority.P2
    project_id: str
    requirement_id: Optional[str] = None
    module_id: Optional[str] = None
    iteration_id: Optional[str] = None
    assignees: Optional[List[str]] = []
    labels: Optional[List[str]] = []
    steps_to_reproduce: Optional[str] = None
    environment: Optional[str] = None


class DefectCreate(DefectBase):
    pass


class DefectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[DefectSeverity] = None
    priority: Optional[DefectPriority] = None
    status: Optional[DefectStatus] = None
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    steps_to_reproduce: Optional[str] = None
    environment: Optional[str] = None
    requirement_id: Optional[str] = None
    module_id: Optional[str] = None
    iteration_id: Optional[str] = None


class DefectCommentCreate(BaseModel):
    content: str


class DefectCommentResponse(BaseModel):
    id: str
    defect_id: str
    user_id: Optional[str]
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class DefectLogResponse(BaseModel):
    id: str
    defect_id: str
    user_id: Optional[str]
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DefectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    severity: DefectSeverity
    priority: DefectPriority
    status: DefectStatus
    project_id: str
    requirement_id: Optional[str]
    module_id: Optional[str]
    iteration_id: Optional[str]
    assignees: List[str]
    labels: List[str]
    steps_to_reproduce: Optional[str]
    environment: Optional[str]
    creator_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    comments: List[DefectCommentResponse] = []
    logs: List[DefectLogResponse] = []

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 运行测试验证**

```bash
cd backend && python -c "from app.schemas.schemas import DefectCreate, DefectResponse, DefectCommentCreate, DefectLogResponse; print('OK')"
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/schemas/schemas.py
git commit -m "feat: add Defect schemas"
```

---

## Task 3: 后端 - 添加 Defect API 路由

**Files:**
- Create: `backend/app/api/defects.py`

**Interfaces:**
- Consumes: Defect, DefectComment, DefectLog 模型
- Produces: defects router with CRUD endpoints

- [ ] **Step 1: 创建 defects.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.models.models import get_db, Defect, DefectComment, DefectLog, DefectStatus
from app.schemas.schemas import (
    DefectCreate, DefectUpdate, DefectResponse,
    DefectCommentCreate, DefectCommentResponse, DefectLogResponse
)
from datetime import datetime

router = APIRouter(prefix="/defects", tags=["defects"])


@router.post("", response_model=DefectResponse, status_code=201)
async def create_defect(data: DefectCreate, db: AsyncSession = Depends(get_db)):
    defect = Defect(**data.model_dump())
    db.add(defect)

    log = DefectLog(
        defect_id=defect.id,
        action="created",
        new_value=f"status={data.severity.value}"
    )
    db.add(log)

    await db.commit()
    await db.refresh(defect)
    return defect


@router.get("", response_model=List[DefectResponse])
async def list_defects(
    project_id: Optional[str] = None,
    status: Optional[DefectStatus] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    creator_id: Optional[str] = None,
    module_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Defect).order_by(desc(Defect.created_at))

    if project_id:
        query = query.where(Defect.project_id == project_id)
    if status:
        query = query.where(Defect.status == status)
    if severity:
        query = query.where(Defect.severity == severity)
    if priority:
        query = query.where(Defect.priority == priority)
    if assignee:
        query = query.where(Defect.assignees.contains(assignee))
    if creator_id:
        query = query.where(Defect.creator_id == creator_id)
    if module_id:
        query = query.where(Defect.module_id == module_id)
    if requirement_id:
        query = query.where(Defect.requirement_id == requirement_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{defect_id}", response_model=DefectResponse)
async def get_defect(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@router.patch("/{defect_id}", response_model=DefectResponse)
async def update_defect(defect_id: str, data: DefectUpdate, db: AsyncSession = Depends(get_db), user_id: Optional[str] = None):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    old_status = defect.status.value if hasattr(defect.status, 'value') else str(defect.status)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(defect, field, value)

    new_status = defect.status.value if hasattr(defect.status, 'value') else str(defect.status)

    if old_status != new_status:
        log = DefectLog(
            defect_id=defect_id,
            user_id=user_id,
            action="status_changed",
            old_value=old_status,
            new_value=new_status
        )
        db.add(log)

    await db.commit()
    await db.refresh(defect)
    return defect


@router.delete("/{defect_id}", status_code=204)
async def delete_defect(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    await db.delete(defect)
    await db.commit()


@router.post("/{defect_id}/comments", response_model=DefectCommentResponse, status_code=201)
async def create_comment(defect_id: str, data: DefectCommentCreate, db: AsyncSession = Depends(get_db), user_id: Optional[str] = None):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Defect not found")

    comment = DefectComment(defect_id=defect_id, user_id=user_id, content=data.content)
    db.add(comment)

    log = DefectLog(defect_id=defect_id, user_id=user_id, action="commented", new_value=data.content[:100])
    db.add(log)

    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/{defect_id}/comments", response_model=List[DefectCommentResponse])
async def list_comments(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DefectComment).where(DefectComment.defect_id == defect_id).order_by(DefectComment.created_at)
    )
    return result.scalars().all()


@router.get("/{defect_id}/logs", response_model=List[DefectLogResponse])
async def list_logs(defect_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DefectLog).where(DefectLog.defect_id == defect_id).order_by(DefectLog.created_at)
    )
    return result.scalars().all()
```

- [ ] **Step 2: 注册 router**

在 `backend/app/api/__init__.py` 添加：
```python
from app.api import defects
```

在 `backend/app/main.py` 添加：
```python
app.include_router(defects.router, prefix=settings.API_PREFIX)
```

- [ ] **Step 3: 运行测试验证**

```bash
cd backend && python -c "from app.api.defects import router; print('OK')"
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/defects.py backend/app/api/__init__.py backend/app/main.py
git commit -m "feat: add Defect API routes"
```

---

## Task 4: 前端 - 添加 API 和 Store

**Files:**
- Modify: `frontend/src/api/index.ts` (添加 defectsApi)
- Create: `frontend/src/stores/defects.ts`

**Interfaces:**
- Consumes: 后端 defects API
- Produces: defectsApi (list, get, create, update, delete, comments, logs)

- [ ] **Step 1: 添加 API**

在 `frontend/src/api/index.ts` 添加：

```typescript
export const defectsApi = {
  list: (params?: {
    project_id?: string
    status?: string
    severity?: string
    priority?: string
    assignee?: string
    creator_id?: string
    module_id?: string
    requirement_id?: string
  }) => request.get('/defects', { params }),

  get: (id: string) => request.get(`/defects/${id}`),

  create: (data: any) => request.post('/defects', data),

  update: (id: string, data: any) => request.patch(`/defects/${id}`, data),

  delete: (id: string) => request.delete(`/defects/${id}`),

  listComments: (id: string) => request.get(`/defects/${id}/comments`),

  createComment: (id: string, data: { content: string }) => request.post(`/defects/${id}/comments`, data),

  listLogs: (id: string) => request.get(`/defects/${id}/logs`),
}
```

- [ ] **Step 2: 创建 store**

创建 `frontend/src/stores/defects.ts`：

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { defectsApi } from '@/api'

export const useDefectsStore = defineStore('defects', () => {
  const defects = ref<any[]>([])
  const currentDefect = ref<any>(null)
  const loading = ref(false)
  const filters = ref({
    project_id: null,
    status: null,
    severity: null,
    priority: null,
    assignee: null,
    creator_id: null,
    module_id: null,
    requirement_id: null,
  })

  const byStatus = computed(() => {
    const groups: Record<string, any[]> = {}
    for (const d of defects.value) {
      const key = d.status
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return groups
  })

  const byPriority = computed(() => {
    const groups: Record<string, any[]> = {}
    for (const d of defects.value) {
      const key = d.priority
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return groups
  })

  const bySeverity = computed(() => {
    const groups: Record<string, any[]> = {}
    for (const d of defects.value) {
      const key = d.severity
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return groups
  })

  const fetchList = async () => {
    loading.value = true
    try {
      const res = await defectsApi.list(filters.value)
      defects.value = res.data
    } finally {
      loading.value = false
    }
  }

  const fetchOne = async (id: string) => {
    loading.value = true
    try {
      const res = await defectsApi.get(id)
      currentDefect.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  return {
    defects, currentDefect, loading, filters,
    byStatus, byPriority, bySeverity,
    fetchList, fetchOne
  }
})
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/index.ts frontend/src/stores/defects.ts
git commit -m "feat: add defects API and store"
```

---

## Task 5: 前端 - 添加路由

**Files:**
- Modify: `frontend/src/router/index.ts`

**Interfaces:**
- Consumes: Defects.vue, DefectDetail.vue, DefectCreate.vue
- Produces: /defects, /defect/new, /defect/:id 路由

- [ ] **Step 1: 添加路由配置**

在 router/index.ts 添加：

```typescript
{
  path: '/defects',
  component: Layout,
  children: [
    { path: '', component: () => import('@/views/Defects.vue') },
    { path: 'new', component: () => import('@/views/DefectCreate.vue') },
    { path: ':id', component: () => import('@/views/DefectDetail.vue') },
  ]
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: add defect routes"
```

---

## Task 6: 前端 - 创建缺陷列表页 Defects.vue

**Files:**
- Create: `frontend/src/views/Defects.vue`

**功能：**
- 顶部筛选栏：项目/状态/严重程度/优先级/负责人/创建人/模块（全部 Filter 下拉）
- 视图切换：列表视图 / 看板视图（默认看板）
- 看板泳道：默认按状态，可切换按优先级/严重程度分组
- 列表视图：可自定义列（标题/状态/严重程度/优先级/负责人/创建人/项目/创建时间）
- 跳转：点击卡片/行跳转 DefectDetail

- [ ] **Step 1: 创建 Defects.vue**

```vue
<template>
  <div class="defects-page">
    <div class="page-header"></div>

    <div class="filters-bar mb-16">
      <el-select v-model="filter.project_id" placeholder="全部项目" style="width:160px;" clearable @change="fetchData">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filter.status" placeholder="全部状态" style="width:130px;" clearable @change="fetchData">
        <el-option value="new" label="新建" />
        <el-option value="confirmed" label="待确认" />
        <el-option value="fixing" label="修复中" />
        <el-option value="verifying" label="待验证" />
        <el-option value="closed" label="已关闭" />
      </el-select>
      <el-select v-model="filter.severity" placeholder="全部严重" style="width:120px;" clearable @change="fetchData">
        <el-option value="fatal" label="致命" />
        <el-option value="critical" label="严重" />
        <el-option value="major" label="一般" />
        <el-option value="minor" label="轻微" />
      </el-select>
      <el-select v-model="filter.priority" placeholder="全部优先级" style="width:120px;" clearable @change="fetchData">
        <el-option value="p0" label="P0" />
        <el-option value="p1" label="P1" />
        <el-option value="p2" label="P2" />
        <el-option value="p3" label="P3" />
      </el-select>
      <el-input v-model="filter.assignee" placeholder="负责人" style="width:120px;" clearable @change="fetchData" />
      <el-input v-model="filter.creator_id" placeholder="创建人" style="width:120px;" clearable @change="fetchData" />
      <el-select v-model="filter.module_id" placeholder="全部模块" style="width:160px;" clearable @change="fetchData">
        <el-option v-for="m in flatModules" :key="m.id" :label="m.path + m.name" :value="m.id" />
      </el-select>
      <el-button type="primary" @click="$router.push('/defect/new')">
        <el-icon><Plus /></el-icon> 新建缺陷
      </el-button>
      <div style="margin-left:auto;">
        <el-radio-group v-model="viewMode">
          <el-radio-button value="kanban">看板</el-radio-button>
          <el-radio-button value="list">列表</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 看板视图 -->
    <div v-if="viewMode === 'kanban'" class="kanban-board">
      <div class="kanban-header">
        <span>泳道：</span>
        <el-radio-group v-model="laneBy" size="small">
          <el-radio-button value="status">状态</el-radio-button>
          <el-radio-button value="priority">优先级</el-radio-button>
          <el-radio-button value="severity">严重程度</el-radio-button>
        </el-radio-group>
      </div>
      <div class="kanban-lanes">
        <div v-for="lane in laneItems" :key="lane.key" class="kanban-lane">
          <div class="lane-title">{{ lane.label }} <span class="lane-count">{{ lane.items.length }}</span></div>
          <div class="lane-cards">
            <div v-for="d in lane.items" :key="d.id" class="defect-card" @click="$router.push(`/defect/${d.id}`)">
              <div class="defect-card-title">{{ d.title }}</div>
              <div class="defect-card-meta">
                <el-tag size="small" :type="severityType(d.severity)">{{ severityLabel(d.severity) }}</el-tag>
                <el-tag size="small">{{ d.priority.toUpperCase() }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <el-card v-else shadow="never">
      <el-table :data="defects" stripe v-loading="loading" @row-click="row => $router.push(`/defect/${row.id}`)">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="severityType(row.severity)">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <span :class="'priority-' + row.priority">{{ row.priority.toUpperCase() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="assignees" label="负责人" width="120">
          <template #default="{ row }">
            <span>{{ formatAssignees(row.assignees) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_id" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { defectsApi, projectsApi, modulesApi } from '@/api'
import { Plus } from '@element-plus/icons-vue'

const projects = ref<any[]>([])
const modules = ref<any[]>([])
const defects = ref<any[]>([])
const loading = ref(false)
const viewMode = ref('kanban')
const laneBy = ref('status')
const filter = ref({
  project_id: null,
  status: null,
  severity: null,
  priority: null,
  assignee: null,
  creator_id: null,
  module_id: null,
})

const flatModules = computed(() => {
  const out: any[] = []
  const walk = (list: any[], depth: number) => {
    for (const m of list) {
      out.push({ ...m, depth })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(modules.value, 0)
  return out
})

const laneConfig = computed(() => {
  if (laneBy.value === 'status') {
    return [
      { key: 'new', label: '新建' },
      { key: 'confirmed', label: '待确认' },
      { key: 'fixing', label: '修复中' },
      { key: 'verifying', label: '待验证' },
      { key: 'closed', label: '已关闭' },
    ]
  }
  if (laneBy.value === 'priority') {
    return [
      { key: 'p0', label: 'P0' },
      { key: 'p1', label: 'P1' },
      { key: 'p2', label: 'P2' },
      { key: 'p3', label: 'P3' },
    ]
  }
  return [
    { key: 'fatal', label: '致命' },
    { key: 'critical', label: '严重' },
    { key: 'major', label: '一般' },
    { key: 'minor', label: '轻微' },
  ]
})

const laneItems = computed(() => {
  return laneConfig.value.map(l => ({
    ...l,
    items: defects.value.filter(d => (d[laneBy.value] === l.key))
  }))
})

const statusLabel = (s: string) => ({ new: '新建', confirmed: '待确认', fixing: '修复中', verifying: '待验证', closed: '已关闭' }[s] || s)
const severityLabel = (s: string) => ({ fatal: '致命', critical: '严重', major: '一般', minor: '轻微' }[s] || s)
const severityType = (s: string) => ({ fatal: 'danger', critical: 'danger', major: 'warning', minor: 'info' }[s] || 'info')
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const formatAssignees = (arr: string[]) => arr?.length ? arr.join(', ') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filter.value.project_id) params.project_id = filter.value.project_id
    if (filter.value.status) params.status = filter.value.status
    if (filter.value.severity) params.severity = filter.value.severity
    if (filter.value.priority) params.priority = filter.value.priority
    if (filter.value.assignee) params.assignee = filter.value.assignee
    if (filter.value.creator_id) params.creator_id = filter.value.creator_id
    if (filter.value.module_id) params.module_id = filter.value.module_id
    const res = await defectsApi.list(params)
    defects.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const [pRes, mRes] = await Promise.all([
    projectsApi.list(),
    modulesApi.list(),
  ])
  projects.value = pRes.data.items ?? pRes.data
  modules.value = mRes.data
  fetchData()
})
</script>

<style scoped>
.filters-bar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.kanban-board { overflow-x:auto; }
.kanban-header { margin-bottom:12px; display:flex; align-items:center; gap:8px; }
.kanban-lanes { display:flex; gap:16px; min-width:max-content; }
.kanban-lane { width:280px; }
.lane-title {
  font-size:13px; font-weight:600; color:#6b7280;
  padding:8px 12px; background:#f9fafb; border-radius:6px 6px 0 0;
  display:flex; align-items:center; gap:8px;
}
.lane-count {
  background:#e5e7eb; border-radius:10px; padding:0 6px;
  font-size:11px; color:#6b7280;
}
.lane-cards { display:flex; flex-direction:column; gap:8px; padding:12px; background:#f3f4f6; border-radius:0 0 8px 8px; min-height:200px; }
.defect-card {
  background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:12px;
  cursor:pointer; transition:box-shadow .15s;
}
.defect-card:hover { box-shadow:0 2px 8px rgba(0,0,0,.1); }
.defect-card-title { font-size:13px; font-weight:500; color:#111827; margin-bottom:8px; }
.defect-card-meta { display:flex; gap:6px; }
.priority-p0 { color:#dc2626; font-weight:700; }
.priority-p1 { color:#ea580c; font-weight:600; }
.priority-p2 { color:#ca8a04; }
.priority-p3 { color:#6b7280; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Defects.vue
git commit -m "feat: add Defects list page with kanban and table views"
```

---

## Task 7: 前端 - 创建缺陷详情页 DefectDetail.vue

**Files:**
- Create: `frontend/src/views/DefectDetail.vue`

**功能：**
- 顶部：标题 + 状态标签 + 操作按钮（修改状态、删除）
- 主体分 Tab：基本信息 / 评论 / 变更日志
- 基本信息：显示所有字段，可编辑
- 评论：列表 + 发表评论
- 变更日志：只读时间线

- [ ] **Step 1: 创建 DefectDetail.vue**

```vue
<template>
  <div class="defect-detail-page">
    <div class="page-header"></div>

    <div v-if="defect" class="defect-content">
      <el-card shadow="never" style="margin-bottom:16px;">
        <template #header>
          <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
            <div>
              <h2 class="detail-title">{{ defect.title }}</h2>
              <div style="display:flex; gap:8px; margin-top:8px; flex-wrap:wrap;">
                <el-tag size="small">{{ statusLabel(defect.status) }}</el-tag>
                <el-tag size="small" :type="severityType(defect.severity)">{{ severityLabel(defect.severity) }}</el-tag>
                <el-tag size="small">{{ defect.priority.toUpperCase() }}</el-tag>
              </div>
            </div>
            <div style="display:flex; gap:8px; flex-shrink:0;">
              <el-select v-model="newStatus" style="width:120px;" @change="changeStatus">
                <el-option value="new" label="新建" />
                <el-option value="confirmed" label="待确认" />
                <el-option value="fixing" label="修复中" />
                <el-option value="verifying" label="待验证" />
                <el-option value="closed" label="已关闭" />
              </el-select>
              <el-button type="primary" @click="showEdit = true">编辑</el-button>
            </div>
          </div>
        </template>

        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="项目">{{ projectName }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ formatAssignees(defect.assignees) }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">{{ severityLabel(defect.severity) }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ defect.priority.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="关联需求">{{ defect.requirement_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联模块">{{ defect.module_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联迭代">{{ defect.iteration_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ defect.labels?.join(', ') || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ defect.creator_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(defect.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="复现步骤" :span="2">{{ defect.steps_to_reproduce || '-' }}</el-descriptions-item>
          <el-descriptions-item label="环境" :span="2">{{ defect.environment || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="defect.description" style="margin-top:16px;">
          <div class="field-label">描述</div>
          <MarkdownRenderer :content="defect.description" />
        </div>
      </el-card>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="评论" name="comments">
          <el-card shadow="never">
            <div v-if="comments.length === 0" style="color:#9ca3af; text-align:center; padding:20px;">暂无评论</div>
            <div v-else class="comment-list">
              <div v-for="c in comments" :key="c.id" class="comment-item">
                <div class="comment-header">
                  <span class="comment-user">{{ c.user_id || '未知用户' }}</span>
                  <span class="comment-time">{{ formatDate(c.created_at) }}</span>
                </div>
                <div class="comment-content">{{ c.content }}</div>
              </div>
            </div>
            <div style="margin-top:16px; display:flex; gap:8px;">
              <el-input v-model="newComment" type="textarea" :rows="2" placeholder="输入评论..." />
              <el-button type="primary" @click="submitComment" :disabled="!newComment.trim()">发送</el-button>
            </div>
          </el-card>
        </el-tab-pane>
        <el-tab-pane label="变更日志" name="logs">
          <el-card shadow="never">
            <el-timeline v-if="logs.length">
              <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="formatDate(log.created_at)" placement="top">
                <div class="log-action">{{ logActionLabel(log.action) }}</div>
                <div v-if="log.old_value || log.new_value" class="log-change">
                  <span v-if="log.old_value">{{ log.old_value }} → </span>{{ log.new_value }}
                </div>
                <div v-if="log.user_id" class="log-user">操作人: {{ log.user_id }}</div>
              </el-timeline-item>
            </el-timeline>
            <div v-else style="color:#9ca3af; text-align:center; padding:20px;">暂无变更记录</div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="showEdit" title="编辑缺陷" width="640px">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <VditorEditor v-model="editForm.description" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="editForm.severity" style="width:100%;">
                <el-option value="fatal" label="致命" />
                <el-option value="critical" label="严重" />
                <el-option value="major" label="一般" />
                <el-option value="minor" label="轻微" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="editForm.priority" style="width:100%;">
                <el-option value="p0" label="P0" />
                <el-option value="p1" label="P1" />
                <el-option value="p2" label="P2" />
                <el-option value="p3" label="P3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="负责人（多人用逗号分隔）">
          <el-input v-model="assigneesInput" placeholder="用户ID，多人用逗号分隔" />
        </el-form-item>
        <el-form-item label="标签（多个用逗号分隔）">
          <el-input v-model="labelsInput" placeholder="标签，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="复现步骤">
          <el-input v-model="editForm.steps_to_reproduce" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="环境">
          <el-input v-model="editForm.environment" placeholder="如: Chrome 120 / Windows 11" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { defectsApi, projectsApi } from '@/api'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import VditorEditor from '@/components/VditorEditor.vue'

const route = useRoute()
const router = useRouter()
const defect = ref<any>(null)
const projects = ref<any[]>([])
const comments = ref<any[]>([])
const logs = ref<any[]>([])
const loading = ref(false)
const activeTab = ref('comments')
const newComment = ref('')
const showEdit = ref(false)
const saving = ref(false)
const newStatus = ref('')
const editForm = ref<any>({})
const assigneesInput = ref('')
const labelsInput = ref('')

const statusLabel = (s: string) => ({ new: '新建', confirmed: '待确认', fixing: '修复中', verifying: '待验证', closed: '已关闭' }[s] || s)
const severityLabel = (s: string) => ({ fatal: '致命', critical: '严重', major: '一般', minor: '轻微' }[s] || s)
const severityType = (s: string) => ({ fatal: 'danger', critical: 'danger', major: 'warning', minor: 'info' }[s] || 'info')
const formatDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '-'
const formatAssignees = (arr: any) => Array.isArray(arr) ? arr.join(', ') : arr || '-'
const logActionLabel = (a: string) => ({ created: '创建缺陷', status_changed: '状态变更', commented: '添加评论', updated: '更新' }[a] || a)

const projectName = computed(() => {
  const p = projects.value.find(x => x.id === defect.value?.project_id)
  return p?.name || defect.value?.project_id || '-'
})

const fetchData = async () => {
  loading.value = true
  try {
    const id = route.params.id as string
    const [defectRes, commentsRes, logsRes, projectsRes] = await Promise.all([
      defectsApi.get(id),
      defectsApi.listComments(id),
      defectsApi.listLogs(id),
      projectsApi.list(),
    ])
    defect.value = defectRes.data
    newStatus.value = defectRes.data.status
    comments.value = commentsRes.data
    logs.value = logsRes.data
    projects.value = projectsRes.data.items ?? projectsRes.data
    editForm.value = { ...defectRes.data }
    assigneesInput.value = (defectRes.data.assignees || []).join(', ')
    labelsInput.value = (defectRes.data.labels || []).join(', ')
  } finally {
    loading.value = false
  }
}

const changeStatus = async () => {
  try {
    await defectsApi.update(route.params.id as string, { status: newStatus.value })
    ElMessage.success('状态已更新')
    fetchData()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const submitComment = async () => {
  try {
    await defectsApi.createComment(route.params.id as string, { content: newComment.value })
    newComment.value = ''
    comments.value = (await defectsApi.listComments(route.params.id as string)).data
    ElMessage.success('评论已发送')
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

const saveEdit = async () => {
  saving.value = true
  try {
    const data: any = { ...editForm.value }
    data.assignees = assigneesInput.value.split(',').map(s => s.trim()).filter(Boolean)
    data.labels = labelsInput.value.split(',').map(s => s.trim()).filter(Boolean)
    await defectsApi.update(route.params.id as string, data)
    showEdit.value = false
    ElMessage.success('保存成功')
    fetchData()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.detail-title { font-size:20px; font-weight:700; color:#1f2329; margin:0; }
.field-label { font-size:12px; font-weight:600; color:#6b7280; margin-bottom:8px; }
.comment-list { display:flex; flex-direction:column; gap:16px; }
.comment-item { padding-bottom:16px; border-bottom:1px solid #f3f4f6; }
.comment-header { display:flex; gap:12px; align-items:center; margin-bottom:6px; }
.comment-user { font-weight:600; font-size:13px; color:#111827; }
.comment-time { font-size:12px; color:#9ca3af; }
.comment-content { font-size:14px; color:#374151; line-height:1.6; }
.log-action { font-weight:600; font-size:13px; color:#111827; }
.log-change { font-size:13px; color:#6b7280; margin-top:4px; }
.log-user { font-size:12px; color:#9ca3af; margin-top:4px; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/DefectDetail.vue
git commit -m "feat: add DefectDetail page with comments and logs"
```

---

## Task 8: 前端 - 创建缺陷创建页 DefectCreate.vue

**Files:**
- Create: `frontend/src/views/DefectCreate.vue`

**功能：**
- 独立页面 `/defect/new`
- 表单：标题、描述（Markdown）、严重程度、优先级、项目、负责人（必填）、关联需求/模块/迭代（可选）、标签、复现步骤、环境
- 创建成功后跳转到缺陷详情页

- [ ] **Step 1: 创建 DefectCreate.vue**

```vue
<template>
  <div class="defect-create-page">
    <div class="page-header"></div>

    <el-card shadow="never">
      <template #header>
        <div style="font-weight:600;">新建缺陷</div>
      </template>

      <el-form :model="form" label-position="top" style="max-width:800px;">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="简要描述缺陷" />
        </el-form-item>

        <el-form-item label="描述">
          <VditorEditor v-model="form.description" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="form.severity" style="width:100%;">
                <el-option value="fatal" label="致命" />
                <el-option value="critical" label="严重" />
                <el-option value="major" label="一般" />
                <el-option value="minor" label="轻微" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width:100%;">
                <el-option value="p0" label="P0 - 紧急" />
                <el-option value="p1" label="P1 - 重要" />
                <el-option value="p2" label="P2 - 一般" />
                <el-option value="p3" label="P3 - 低" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="所属项目" required>
          <el-select v-model="form.project_id" style="width:100%;" placeholder="选择项目">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="负责人（多人用逗号分隔）" required>
          <el-input v-model="assigneesInput" placeholder="用户ID，多人用逗号分隔" />
        </el-form-item>

        <el-divider content-position="left">关联信息（非必填）</el-divider>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="关联需求">
              <el-input v-model="form.requirement_id" placeholder="需求ID" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关联模块">
              <el-select v-model="form.module_id" style="width:100%;" placeholder="选择模块" clearable>
                <el-option v-for="m in flatModules" :key="m.id" :label="m.path + m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关联迭代">
              <el-select v-model="form.iteration_id" style="width:100%;" placeholder="选择迭代" clearable>
                <el-option v-for="i in iterations" :key="i.id" :label="i.name" :value="i.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="标签（多个用逗号分隔）">
          <el-input v-model="labelsInput" placeholder="如: UI, 后端, 回归" />
        </el-form-item>

        <el-form-item label="复现步骤">
          <el-input v-model="form.steps_to_reproduce" type="textarea" :rows="4" placeholder="1. ...\n2. ...\n3. ..." />
        </el-form-item>

        <el-form-item label="环境">
          <el-input v-model="form.environment" placeholder="如: Chrome 120 / Windows 11 / iOS 17" />
        </el-form-item>

        <el-form-item>
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" @click="submit" :loading="saving" :disabled="!form.title.trim() || !form.project_id || !assigneesInput.trim()">
            创建缺陷
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { defectsApi, projectsApi, modulesApi, iterationsApi } from '@/api'
import { ElMessage } from 'element-plus'
import VditorEditor from '@/components/VditorEditor.vue'

const router = useRouter()
const projects = ref<any[]>([])
const modules = ref<any[]>([])
const iterations = ref<any[]>([])
const saving = ref(false)
const assigneesInput = ref('')
const labelsInput = ref('')
const form = ref({
  title: '',
  description: '',
  severity: 'major',
  priority: 'p2',
  project_id: '',
  requirement_id: '',
  module_id: null,
  iteration_id: null,
  steps_to_reproduce: '',
  environment: '',
})

const flatModules = computed(() => {
  const out: any[] = []
  const walk = (list: any[], depth: number) => {
    for (const m of list) {
      out.push({ ...m, depth })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(modules.value, 0)
  return out
})

const submit = async () => {
  saving.value = true
  try {
    const data: any = { ...form.value }
    data.assignees = assigneesInput.value.split(',').map(s => s.trim()).filter(Boolean)
    data.labels = labelsInput.value.split(',').map(s => s.trim()).filter(Boolean)
    const res = await defectsApi.create(data)
    ElMessage.success('缺陷已创建')
    router.push(`/defect/${res.data.id}`)
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const [pRes, mRes, iRes] = await Promise.all([
    projectsApi.list(),
    modulesApi.list(),
    iterationsApi.list(),
  ])
  projects.value = pRes.data.items ?? pRes.data
  modules.value = mRes.data
  iterations.value = iRes.data.items ?? iRes.data
})
</script>

<style scoped>
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/DefectCreate.vue
git commit -m "feat: add DefectCreate page"
```

---

## 自检清单

- [ ] 所有枚举状态都已定义
- [ ] Defect 模型包含所有字段
- [ ] API 支持所有筛选参数
- [ ] 列表页支持看板和列表切换
- [ ] 看板支持按状态/优先级/严重程度切换泳道
- [ ] 详情页包含基本信息、评论、变更日志三个 Tab
- [ ] 创建页使用独立页面而非弹窗
- [ ] 负责人为必填
- [ ] 状态变更记录日志
