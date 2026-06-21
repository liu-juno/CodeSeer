<template>
  <div class="projects-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">项目管理</h1>
        <el-text class="text-muted" style="margin-left:12px;">{{ total }} 个项目</el-text>
      </div>
      <div class="header-right">
        <el-input v-model="search" placeholder="搜索项目..." style="width:200px;" clearable @input="onSearch" />
        <el-button type="primary" @click="showCreateModal = true">
          <el-icon><Plus /></el-icon> 创建项目
        </el-button>
      </div>
    </div>

    <el-table :data="filteredProjects" stripe style="width:100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="name" label="项目名称" min-width="180">
        <template #default="{ row }">
          <el-link type="primary" underline="never" @click="$router.push(`/project/${row.id}`)">
            {{ row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="identifier" label="标识符" width="160">
        <template #default="{ row }">
          <span v-if="row.identifier" class="identifier-badge">{{ row.identifier }}</span>
          <el-button v-else size="small" text type="warning" @click="openEdit(row)">⚠ 未设置</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          <el-text class="text-muted">{{ row.description || '—' }}</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">
          <el-text class="text-muted text-small">{{ formatDate(row.created_at) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="$router.push(`/project/${row.id}`)">查看</el-button>
          <el-button size="small" text @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="deleteProject(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      background
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @size-change="onSizeChange"
      @current-change="onPageChange"
      style="margin-top: 20px; justify-content: flex-end;"
    />

    <!-- 创建对话框 -->
    <el-dialog v-model="showCreateModal" title="创建项目" width="520px" @closed="resetForm">
      <el-form :model="form" label-position="top">
        <el-form-item label="项目名称" required>
          <el-input v-model="form.name" placeholder="如：CodeSeer Web" />
        </el-form-item>
        <el-form-item label="项目标识符" required :error="identifierError">
          <el-input
            v-model="form.identifier"
            placeholder="如：codeseer-web（小写字母、数字、连字符）"
            @input="validateIdentifier"
          />
          <div class="field-hint">用于文档路径和 AI 工具引用</div>
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" placeholder="简要描述项目目标..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateModal = false">取消</el-button>
        <el-button type="primary" :disabled="!form.name.trim() || !form.identifier.trim() || !!identifierError" :loading="saving" @click="createProject">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditModal" title="编辑项目" width="520px" @closed="resetForm">
      <el-form :model="form" label-position="top">
        <el-form-item label="项目名称" required>
          <el-input v-model="form.name" placeholder="项目名称" />
        </el-form-item>
        <el-form-item label="项目标识符" required :error="identifierError">
          <el-input
            v-model="form.identifier"
            placeholder="如：codeseer-web（小写字母、数字、连字符）"
            @input="validateIdentifier"
          />
          <div class="field-hint">用于文档路径，全局唯一，只能包含小写字母、数字和连字符</div>
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" placeholder="简要描述项目目标..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditModal = false">取消</el-button>
        <el-button type="primary" :disabled="!form.name.trim() || !form.identifier.trim() || !!identifierError" :loading="saving" @click="updateProject">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { projectsApi } from '@/api'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const { items, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange } = usePagination(
  async (p, ps) => {
    const res = await projectsApi.list(p, ps)
    return { items: res.data.items, total: res.data.total }
  }
)

const saving = ref(false)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingId = ref<string | null>(null)
const search = ref('')

const form = ref({ name: '', identifier: '', description: '' })
const identifierError = ref('')

const onSearch = () => fetchPage(1)

const validateIdentifier = () => {
  const v = form.value.identifier
  if (!v) { identifierError.value = ''; return }
  if (!/^[a-z][a-z0-9-]{1,48}[a-z0-9]$/.test(v)) {
    identifierError.value = '只能包含小写字母、数字和连字符，长度 3-50，首尾为字母或数字'
  } else {
    identifierError.value = ''
  }
}

const resetForm = () => {
  form.value = { name: '', identifier: '', description: '' }
  identifierError.value = ''
  editingId.value = null
}

const openCreate = () => {
  resetForm()
  showCreateModal.value = true
}

const openEdit = (row: any) => {
  resetForm()
  editingId.value = row.id
  form.value = { name: row.name, identifier: row.identifier || '', description: row.description || '' }
  showEditModal.value = true
}

const handleSelectionChange = (_rows: any[]) => {}

const filteredProjects = computed(() => {
  if (!search.value.trim()) return items.value
  const q = search.value.trim().toLowerCase()
  return items.value.filter((p: any) => p.name.toLowerCase().includes(q))
})

const statusType = (s: string) => ({ active: 'primary', archived: 'info', completed: 'success' }[s] || 'info')
const statusText = (s: string) => ({ active: '进行中', archived: '已归档', completed: '已完成' }[s] || s)
const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

const createProject = async () => {
  if (identifierError.value) return
  saving.value = true
  try {
    await projectsApi.create({
      name: form.value.name,
      identifier: form.value.identifier,
      description: form.value.description,
    })
    showCreateModal.value = false
    ElMessage.success('创建成功')
    fetchPage(page.value)
  } catch (e: any) {
    if (e?.response?.status === 409) identifierError.value = '该标识符已被其他项目使用'
    else console.error(e)
  } finally { saving.value = false }
}

const updateProject = async () => {
  if (!editingId.value || identifierError.value) return
  saving.value = true
  try {
    await projectsApi.update(editingId.value, {
      name: form.value.name,
      identifier: form.value.identifier,
      description: form.value.description,
    })
    showEditModal.value = false
    ElMessage.success('保存成功')
    fetchPage(page.value)
  } catch (e: any) {
    if (e?.response?.status === 409) identifierError.value = '该标识符已被其他项目使用'
    else console.error(e)
  } finally { saving.value = false }
}

const deleteProject = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除此项目？', '提示', { type: 'warning' })
    await projectsApi.delete(id)
    ElMessage.success('删除成功')
    fetchPage(page.value)
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

onMounted(() => fetchPage(1))
</script>

<style scoped>
.projects-page { max-width: 1200px; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-left, .header-right { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; margin: 0; }
.identifier-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  color: var(--el-text-color-secondary);
}
.field-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
