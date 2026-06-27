# 项目权限改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现基于项目的权限系统，用户需先选择项目才能操作该项目下的内容

**Architecture:** 新增 `project_members` 表存储项目成员关系，在 API 层添加项目成员检查，前端新增项目选择页和项目上下文状态

**Tech Stack:** FastAPI + SQLAlchemy + Vue 3 + Element Plus

## Global Constraints

- MySQL 数据库，密码 `@` 字符需 URL 编码
- 后端端口 8000，前端端口 3000
- 使用 aiomysql 异步驱动
- 角色标签：admin/dev/test/product，不做权限限制

---

## File Structure

### Backend Changes

| File | Responsibility |
|------|----------------|
| `backend/app/models/models.py` | 新增 `ProjectMember` model |
| `backend/app/schemas/schemas.py` | 新增 `ProjectMember` Pydantic schemas |
| `backend/app/api/projects.py` | 项目成员管理 API、申请/审核 API |
| `backend/app/api/requirements.py` | 添加项目成员检查 |
| `backend/app/api/iterations.py` | 添加项目成员检查 |
| `backend/app/api/defects.py` | 添加项目成员检查 |
| `backend/app/api/mcp_handlers.py` | 添加项目成员检查 |
| `backend/app/core/database.py` | 无变更（已支持 MySQL）|
| `backend/app/core/auth.py` | 可选：新增项目上下文依赖 |
| `init_sql_mysql.sql` | 新增 `project_members` 表 |

### Frontend Changes

| File | Responsibility |
|------|----------------|
| `frontend/src/stores/project.ts` | 新增：当前项目上下文状态 |
| `frontend/src/router/index.ts` | 添加项目路由守卫 |
| `frontend/src/views/ProjectSelect.vue` | 新增：项目选择页面 |
| `frontend/src/views/ProjectSettings.vue` | 新增/改造：项目设置（含成员管理）|
| `frontend/src/api/index.ts` | 添加项目成员 API |
| `frontend/src/components/Layout.vue` | 添加项目切换按钮 |

---

## Task 1: 创建 `project_members` 数据表

**Files:**
- Modify: `init_sql_mysql.sql`

**SQL:**
```sql
CREATE TABLE IF NOT EXISTS project_members (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'dev',
    status VARCHAR(20) NOT NULL DEFAULT 'approved',
    invited_by VARCHAR(36),
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id),
    UNIQUE KEY uk_project_user (project_id, user_id),
    KEY idx_project_members_project_id (project_id),
    KEY idx_project_members_user_id (user_id)
);
```

- [ ] **Step 1: 执行 SQL 创建表**

```bash
/opt/anaconda3/bin/mysql -u root -pljb0916@ codeseer -e "
CREATE TABLE IF NOT EXISTS project_members (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'dev',
    status VARCHAR(20) NOT NULL DEFAULT 'approved',
    invited_by VARCHAR(36),
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id),
    UNIQUE KEY uk_project_user (project_id, user_id),
    KEY idx_project_members_project_id (project_id),
    KEY idx_project_members_user_id (user_id)
);"
```

- [ ] **Step 2: 添加外键约束**

```bash
/opt/anaconda3/bin/mysql -u root -pljb0916@ codeseer -e "
ALTER TABLE project_members ADD CONSTRAINT fk_project_members_project FOREIGN KEY (project_id) REFERENCES projects(id);
ALTER TABLE project_members ADD CONSTRAINT fk_project_members_user FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE project_members ADD CONSTRAINT fk_project_members_invited_by FOREIGN KEY (invited_by) REFERENCES users(id);"
```

---

## Task 2: 创建 `ProjectMember` Model

**Files:**
- Modify: `backend/app/models/models.py`

**Interfaces:**
- Produces: `ProjectMember` SQLAlchemy model with fields: id, project_id, user_id, role, status, invited_by, created_at, updated_at

- [ ] **Step 1: 在 models.py 末尾添加 ProjectMember model**

```python
class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False, default="dev")  # admin/dev/test/product
    status = Column(String(20), nullable=False, default="approved")  # pending/approved/rejected
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uk_project_user'),
    )
```

- [ ] **Step 2: 在 Project model 中添加反向关系**

在 `Project` class 中添加：
```python
members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
```

- [ ] **Step 3: 在 User model 中添加反向关系**

在 `User` class 中添加：
```python
project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
```

- [ ] **Step 4: 验证 models 能正常导入**

```bash
cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && source venv/bin/activate && python3 -c "from app.models.models import ProjectMember; print('OK')"
```

---

## Task 3: 创建 `ProjectMember` Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas/schemas.py`

**Interfaces:**
- Produces: `ProjectMemberCreate`, `ProjectMemberResponse`, `ProjectMemberUpdate` Pydantic models

- [ ] **Step 1: 在 schemas.py 末尾添加 ProjectMember schemas**

```python
class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = "dev"
    invited_by: Optional[str] = None

class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None

class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    status: str
    invited_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 验证 schemas 能正常导入**

```bash
cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && source venv/bin/activate && python3 -c "from app.schemas.schemas import ProjectMemberResponse; print('OK')"
```

---

## Task 4: 创建项目成员管理 API

**Files:**
- Modify: `backend/app/api/projects.py`

**Interfaces:**
- Produces: `GET /projects/:id/members` - 列出项目成员
- Produces: `POST /projects/:id/members` - 添加项目成员（管理员）
- Produces: `DELETE /projects/:id/members/:user_id` - 移除项目成员（管理员）
- Produces: `PATCH /projects/:id/members/:user_id` - 更新成员角色/状态
- Produces: `POST /projects/:id/apply` - 申请加入项目
- Produces: `POST /projects/:id/approve/:user_id` - 批准申请
- Produces: `POST /projects/:id/reject/:user_id` - 拒绝申请
- Produces: `GET /projects/mine` - 获取我的项目列表

- [ ] **Step 1: 添加项目成员相关 API 端点到 projects.py**

在文件末尾添加：

```python
@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
async def list_project_members(project_id: str, db: AsyncSession = Depends(get_db)):
    """列出项目所有成员"""
    result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    members = result.scalars().all()
    response = []
    for m in members:
        user_result = await db.execute(select(User).where(User.id == m.user_id))
        user = user_result.scalar_one_or_none()
        response.append(ProjectMemberResponse(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            role=m.role,
            status=m.status,
            invited_by=m.invited_by,
            created_at=m.created_at,
            updated_at=m.updated_at,
            user_name=user.name if user else None,
            user_email=user.email if user else None
        ))
    return response

@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(project_id: str, member: ProjectMemberCreate, db: AsyncSession = Depends(get_db)):
    """管理员添加项目成员（直接成为 approved）"""
    # 检查用户是否存在
    user_result = await db.execute(select(User).where(User.id == member.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已是成员
    existing = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == member.user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该用户已是项目成员")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=member.user_id,
        role=member.role,
        status="approved",
        invited_by=member.invited_by
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return ProjectMemberResponse(
        id=new_member.id,
        project_id=new_member.project_id,
        user_id=new_member.user_id,
        role=new_member.role,
        status=new_member.status,
        invited_by=new_member.invited_by,
        created_at=new_member.created_at,
        updated_at=new_member.updated_at,
        user_name=user.name,
        user_email=user.email
    )

@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(project_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """管理员移除项目成员"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    await db.delete(member)
    await db.commit()
    return {"message": "成员已移除"}

@router.patch("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_project_member(project_id: str, user_id: str, update: ProjectMemberUpdate, db: AsyncSession = Depends(get_db)):
    """更新项目成员角色或状态"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    if update.role is not None:
        member.role = update.role
    if update.status is not None:
        member.status = update.status
    await db.commit()
    await db.refresh(member)
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        invited_by=member.invited_by,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.post("/projects/{project_id}/apply", response_model=ProjectMemberResponse)
async def apply_to_project(project_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """用户申请加入项目"""
    # 检查项目是否存在
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已是成员
    existing = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已是项目成员")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=current_user.id,
        role="dev",
        status="pending"
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return ProjectMemberResponse(
        id=new_member.id,
        project_id=new_member.project_id,
        user_id=new_member.user_id,
        role=new_member.role,
        status=new_member.status,
        invited_by=new_member.invited_by,
        created_at=new_member.created_at,
        updated_at=new_member.updated_at,
        user_name=current_user.name,
        user_email=current_user.email
    )

@router.post("/projects/{project_id}/approve/{user_id}", response_model=ProjectMemberResponse)
async def approve_project_member(project_id: str, user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """项目创建人或管理员批准申请"""
    # 检查权限
    if not await check_project_admin(project_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="需要项目管理员权限")

    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="申请不存在")
    member.status = "approved"
    await db.commit()
    await db.refresh(member)
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        invited_by=member.invited_by,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.post("/projects/{project_id}/reject/{user_id}")
async def reject_project_member(project_id: str, user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """项目创建人或管理员拒绝申请"""
    if not await check_project_admin(project_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="需要项目管理员权限")

    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="申请不存在")
    await db.delete(member)
    await db.commit()
    return {"message": "已拒绝申请"}

@router.get("/projects/mine", response_model=List[ProjectResponse])
async def get_my_projects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户参与的所有项目"""
    result = await db.execute(
        select(Project).join(ProjectMember).where(ProjectMember.user_id == current_user.id)
    )
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]
```

- [ ] **Step 2: 添加 check_project_admin 辅助函数**

在文件顶部添加辅助函数：

```python
async def check_project_admin(project_id: str, user_id: str, db: AsyncSession) -> bool:
    """检查用户是否是项目管理员或创建人"""
    # 检查是否是项目创建人
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project and project.owner_id == user_id:
        return True
    # 检查是否是项目管理员
    member_result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role == "admin",
                ProjectMember.status == "approved"
            )
        )
    )
    return member_result.scalar_one_or_none() is not None
```

- [ ] **Step 3: 添加 check_project_member 辅助函数**

```python
async def check_project_member(project_id: str, user_id: str, db: AsyncSession) -> bool:
    """检查用户是否是项目成员"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.status == "approved"
            )
        )
    )
    return result.scalar_one_or_none() is not None
```

- [ ] **Step 4: 验证 API 能正常加载**

```bash
cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && source venv/bin/activate && python3 -c "from app.api.projects import router; print('OK')"
```

---

## Task 5: 在项目相关 API 添加成员检查

**Files:**
- Modify: `backend/app/api/requirements.py`
- Modify: `backend/app/api/iterations.py`
- Modify: `backend/app/api/defects.py`

**Interfaces:**
- 所有查询和操作需检查用户是否是项目成员
- 非成员返回 403 Forbidden

- [ ] **Step 1: 修改 requirements.py 添加成员检查**

在 `list_requirements` 函数中添加：
```python
@router.get("/requirements")
async def list_requirements(
    project_id: Optional[str] = None,
    iteration_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if project_id:
        if not await check_project_member(project_id, current_user.id, db):
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    # ... rest of the function
```

同样在 `create_requirement`, `get_requirement`, `update_requirement`, `delete_requirement` 中添加检查。

- [ ] **Step 2: 修改 iterations.py 添加成员检查**

类似 requirements.py，在所有端点添加 `project_id` 参数并检查成员身份。

- [ ] **Step 3: 修改 defects.py 添加成员检查**

类似 requirements.py，在所有端点添加 `project_id` 参数并检查成员身份。

---

## Task 6: 创建 Project Store

**Files:**
- Create: `frontend/src/stores/project.ts`

**Interfaces:**
- Produces: `useProjectStore` Pinia store
- State: `currentProjectId`, `currentProject`, `myProjects`
- Actions: `setCurrentProject`, `clearCurrentProject`, `fetchMyProjects`

- [ ] **Step 1: 创建 project store**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref<string | null>(null)
  const currentProject = ref<any | null>(null)
  const myProjects = ref<any[]>([])

  const hasProject = computed(() => !!currentProjectId.value)

  function setCurrentProject(project: any) {
    currentProject.value = project
    currentProjectId.value = project.id
    localStorage.setItem('currentProjectId', project.id)
  }

  function clearCurrentProject() {
    currentProject.value = null
    currentProjectId.value = null
    localStorage.removeItem('currentProjectId')
  }

  async function fetchMyProjects() {
    const res = await projectsApi.getMine()
    myProjects.value = res.data
    return myProjects.value
  }

  function initFromStorage() {
    const stored = localStorage.getItem('currentProjectId')
    if (stored) {
      currentProjectId.value = stored
    }
  }

  return {
    currentProjectId,
    currentProject,
    myProjects,
    hasProject,
    setCurrentProject,
    clearCurrentProject,
    fetchMyProjects,
    initFromStorage
  }
})
```

---

## Task 7: 更新 API 添加项目成员接口

**Files:**
- Modify: `frontend/src/api/index.ts`

**Interfaces:**
- Produces: `projectsApi.getMine()`, `projectsApi.listMembers(projectId)`, `projectsApi.addMember(projectId, data)`, `projectsApi.removeMember(projectId, userId)`, `projectsApi.applyToProject(projectId)`, `projectsApi.approveMember(projectId, userId)`, `projectsApi.rejectMember(projectId, userId)`

- [ ] **Step 1: 在 projectsApi 中添加成员相关方法**

```typescript
export const projectsApi = {
  // ... existing methods ...

  getMine: () => api.get('/projects/mine'),

  listMembers: (projectId: string) => api.get(`/projects/${projectId}/members`),

  addMember: (projectId: string, data: { user_id: string; role: string }) =>
    api.post(`/projects/${projectId}/members`, data),

  removeMember: (projectId: string, userId: string) =>
    api.delete(`/projects/${projectId}/members/${userId}`),

  updateMember: (projectId: string, userId: string, data: { role?: string; status?: string }) =>
    api.patch(`/projects/${projectId}/members/${userId}`, data),

  applyToProject: (projectId: string) => api.post(`/projects/${projectId}/apply`),

  approveMember: (projectId: string, userId: string) =>
    api.post(`/projects/${projectId}/approve/${userId}`),

  rejectMember: (projectId: string, userId: string) =>
    api.post(`/projects/${projectId}/reject/${userId}`),
}
```

---

## Task 8: 创建项目选择页面

**Files:**
- Create: `frontend/src/views/ProjectSelect.vue`

**Interfaces:**
- Route: `/projects/select`
- Tabs: "我的项目" / "全部项目"
- Project cards with apply/enter button

- [ ] **Step 1: 创建 ProjectSelect.vue**

```vue
<template>
  <div class="project-select-page">
    <div class="page-header">
      <h2>选择项目</h2>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="我的项目" name="mine">
        <div v-if="myProjects.length === 0" class="empty-tip">
          暂无参与的项目
        </div>
        <div v-else class="project-grid">
          <div
            v-for="project in myProjects"
            :key="project.id"
            class="project-card"
            @click="enterProject(project)"
          >
            <div class="project-icon">{{ project.name.charAt(0) }}</div>
            <div class="project-name">{{ project.name }}</div>
            <div class="project-desc">{{ project.description || '暂无描述' }}</div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="全部项目" name="all">
        <div class="project-grid">
          <div
            v-for="project in allProjects"
            :key="project.id"
            class="project-card"
          >
            <div class="project-icon">{{ project.name.charAt(0) }}</div>
            <div class="project-name">{{ project.name }}</div>
            <div class="project-desc">{{ project.description || '暂无描述' }}</div>
            <div class="project-actions">
              <template v-if="isMyProject(project.id)">
                <el-button type="primary" size="small" @click="enterProject(project)">
                  进入
                </el-button>
              </template>
              <template v-else-if="isPending(project.id)">
                <el-tag type="warning">待审核</el-tag>
              </template>
              <template v-else>
                <el-button type="outline" size="small" @click="applyToProject(project)">
                  申请加入
                </el-button>
              </template>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()

const activeTab = ref('mine')
const myProjects = ref<any[]>([])
const allProjects = ref<any[]>([])
const pendingProjects = ref<Set<string>>(new Set())

onMounted(async () => {
  await loadProjects()
})

async function loadProjects() {
  myProjects.value = await projectStore.fetchMyProjects()
  const res = await projectsApi.list({ page: 1, page_size: 100 })
  allProjects.value = res.data.items || res.data
}

function isMyProject(projectId: string): boolean {
  return myProjects.value.some(p => p.id === projectId)
}

function isPending(projectId: string): boolean {
  return pendingProjects.value.has(projectId)
}

async function applyToProject(project: any) {
  try {
    await projectsApi.applyToProject(project.id)
    ElMessage.success('申请已提交，请等待审核')
    pendingProjects.value.add(project.id)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '申请失败')
  }
}

function enterProject(project: any) {
  projectStore.setCurrentProject(project)
  router.push('/dashboard')
}
</script>

<style scoped>
.project-select-page {
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.project-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.project-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.project-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #6366f1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
}
.project-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.project-desc {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}
.empty-tip {
  text-align: center;
  padding: 48px;
  color: #9ca3af;
}
</style>
```

---

## Task 9: 更新路由守卫

**Files:**
- Modify: `frontend/src/router/index.ts`

**Interfaces:**
- `/projects/select` 无需守卫（公开）
- 其他路由需先选择项目才能访问
- 未选择项目时跳转 `/projects/select`

- [ ] **Step 1: 更新路由守卫**

```typescript
router.beforeEach(async (to) => {
  // 公开路由
  if (to.meta.public) return true

  const auth = useAuthStore()
  if (!auth.isLoggedIn) {
    return { name: 'login' }
  }

  // 不需要项目的路由
  const noProjectRoutes = ['project-select', 'login', 'register']
  if (noProjectRoutes.includes(to.name as string)) return true

  // 检查是否已选择项目
  const projectStore = useProjectStore()
  projectStore.initFromStorage()

  if (!projectStore.currentProjectId) {
    return { name: 'project-select' }
  }

  return true
})
```

- [ ] **Step 2: 添加 project-select 路由**

```typescript
{
  path: '/projects/select',
  name: 'project-select',
  component: () => import('@/views/ProjectSelect.vue'),
  meta: { public: true }
}
```

---

## Task 10: 更新 Layout 添加项目切换

**Files:**
- Modify: `frontend/src/components/Layout.vue`

**Interfaces:**
- 顶部栏添加项目切换按钮
- 点击弹出项目选择或快速切换

- [ ] **Step 1: 在顶部栏添中项目切换按钮**

在顶部栏 `TopTab` 位置添加：

```vue
<div class="project-switcher" @click="goToProjectSelect">
  <el-icon><Folder /></el-icon>
  <span>{{ projectStore.currentProject?.name || '选择项目' }}</span>
  <el-icon><ArrowDown /></el-icon>
</div>
```

```typescript
import { useProjectStore } from '@/stores/project'
const projectStore = useProjectStore()

function goToProjectSelect() {
  router.push('/projects/select')
}
```

---

## Task 11: 创建项目设置页面（成员管理）

**Files:**
- Create: `frontend/src/views/ProjectSettings.vue`

**Interfaces:**
- Route: `/project/:id/settings`
- Tab: 成员管理 - 列表、添加、移除、修改角色
- 显示待审核申请，可批准/拒绝

- [ ] **Step 1: 创建 ProjectSettings.vue**

```vue
<template>
  <div class="project-settings-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="成员管理" name="members">
        <div class="section-header">
          <h3>项目成员</h3>
          <el-button type="primary" @click="showAddDialog = true">
            添加成员
          </el-button>
        </div>

        <el-table :data="members" stripe>
          <el-table-column prop="user_name" label="姓名" />
          <el-table-column prop="user_email" label="邮箱" />
          <el-table-column prop="role" label="角色">
            <template #default="{ row }">
              <el-select v-model="row.role" @change="updateRole(row)">
                <el-option label="管理员" value="admin" />
                <el-option label="开发" value="dev" />
                <el-option label="测试" value="test" />
                <el-option label="产品" value="product" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="{ row }">
              <el-tag :type="row.status === 'approved' ? 'success' : 'warning'">
                {{ row.status === 'approved' ? '已加入' : '待审核' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <template v-if="row.status === 'pending'">
                <el-button size="small" type="success" @click="approve(row)">批准</el-button>
                <el-button size="small" type="danger" @click="reject(row)">拒绝</el-button>
              </template>
              <el-button v-else size="small" type="danger" @click="remove(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showAddDialog" title="添加成员" width="400px">
      <el-form :model="addForm">
        <el-form-item label="用户邮箱">
          <el-input v-model="addForm.email" placeholder="输入用户邮箱" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="addForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="开发" value="dev" />
            <el-option label="测试" value="test" />
            <el-option label="产品" value="product" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, usersApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const projectId = route.params.id as string

const activeTab = ref('members')
const members = ref<any[]>([])
const showAddDialog = ref(false)
const addForm = ref({ email: '', role: 'dev' })
const users = ref<any[]>([])

onMounted(() => {
  loadMembers()
  loadUsers()
})

async function loadMembers() {
  const res = await projectsApi.listMembers(projectId)
  members.value = res.data
}

async function loadUsers() {
  const res = await usersApi.list({ page: 1, page_size: 100 })
  users.value = res.data.items || res.data
}

async function addMember() {
  const user = users.value.find(u => u.email === addForm.value.email)
  if (!user) {
    ElMessage.error('用户不存在')
    return
  }
  try {
    await projectsApi.addMember(projectId, { user_id: user.id, role: addForm.value.role })
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadMembers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

async function updateRole(row: any) {
  await projectsApi.updateMember(projectId, row.user_id, { role: row.role })
  ElMessage.success('更新成功')
}

async function remove(row: any) {
  await projectsApi.removeMember(projectId, row.user_id)
  ElMessage.success('已移除')
  loadMembers()
}

async function approve(row: any) {
  await projectsApi.approveMember(projectId, row.user_id)
  ElMessage.success('已批准')
  loadMembers()
}

async function reject(row: any) {
  await projectsApi.rejectMember(projectId, row.user_id)
  ElMessage.success('已拒绝')
  loadMembers()
}
</script>

<style scoped>
.project-settings-page {
  padding: 24px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
```

---

## Task 12: 更新路由添加项目设置

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 添加项目设置路由**

```typescript
{
  path: '/project/:id/settings',
  component: () => import('@/views/ProjectSettings.vue')
}
```

---

## Task 13: 验证和测试

- [ ] **Step 1: 重启后端服务**

```bash
pkill -f uvicorn; sleep 2
cd /Users/liujunbo/AI/code/SeerForge/CodeSeer/backend && source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 3
curl -s http://localhost:8000/docs | head -3
```

- [ ] **Step 2: 测试 API**

```bash
# 测试获取我的项目
curl -s http://localhost:8000/api/projects/mine -H "Authorization: Bearer <token>"

# 测试获取项目成员
curl -s http://localhost:8000/api/projects/<project_id>/members -H "Authorization: Bearer <token>"
```

- [ ] **Step 3: 测试前端**

访问 http://localhost:3000 应该跳转到项目选择页

---

## 实施顺序

1. Task 1-3: 数据库和 Model 层
2. Task 4-5: API 层
3. Task 6-7: 前端 Store 和 API
4. Task 8-12: 前端页面和路由
5. Task 13: 测试验证