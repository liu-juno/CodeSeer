<template>
  <div class="requirements-page">
    <div class="page-header">
      <div class="header-right">
        <el-input v-model="filter.search" placeholder="搜索需求..." style="width:200px;" clearable @input="onFilterChange" />
        <el-select v-model="filter.status" placeholder="全部状态" style="width:130px" clearable @change="onFilterChange">
          <el-option value="draft" label="草稿" />
          <el-option value="assigned" label="已指派" />
          <el-option value="in_progress" label="开发中" />
          <el-option value="pending_review" label="待评审" />
          <el-option value="review_approved" label="评审通过" />
          <el-option value="review_rejected" label="评审驳回" />
          <el-option value="completed" label="已完成" />
        </el-select>
        <el-select v-model="filter.priority" placeholder="全部优先级" style="width:100px" clearable @change="onFilterChange">
          <el-option value="P0" label="P0" />
          <el-option value="P1" label="P1" />
          <el-option value="P2" label="P2" />
          <el-option value="P3" label="P3" />
        </el-select>
        <el-button type="primary" @click="$router.push('/requirement/new')">
          <el-icon><Plus /></el-icon> 创建需求
        </el-button>
      </div>
    </div>

    <el-table :data="displayedRequirements" stripe style="width:100%">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="title" label="需求标题" min-width="240">
        <template #default="{ row }">
          <el-link type="primary" underline="never" @click="$router.push(`/requirement/${row.id}`)">
            {{ row.title }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small" effect="plain">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="iteration_id" label="迭代" width="140">
        <template #default="{ row }">
          <el-text class="text-muted">{{ getIterationName(row.iteration_id) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="开发人员" width="150">
        <template #default="{ row }">
          <div v-if="row.assignee_id" style="display:flex; align-items:center; gap:6px;">
            <span class="assignee-badge">{{ userNameById(row.assignee_id) }}</span>
            <el-button size="small" text @click="openAssign(row)" style="padding:0; min-height:0;">✎</el-button>
          </div>
          <el-button v-else size="small" text type="primary" @click="openAssign(row)">+ 指派</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="110">
        <template #default="{ row }">
          <el-text class="text-muted text-small">{{ formatDate(row.created_at) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" align="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="$router.push(`/requirement/${row.id}`)">查看</el-button>
          <el-button size="small" text type="danger" @click="deleteRequirement(row.id)">删除</el-button>
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

    <el-dialog v-model="showAssignDialog" title="指派开发人员" width="420px">
      <el-form label-position="top">
        <el-form-item label="选择开发人员">
          <el-select v-model="assignInput" placeholder="请选择开发人员" style="width:100%" filterable>
            <el-option
              v-for="u in users"
              :key="u.id"
              :value="u.id"
              :label="u.name"
            >
              <div style="display:flex; align-items:center; gap:8px;">
                <span
                  :style="`width:26px;height:26px;border-radius:50%;background:${u.avatar_color||'#6366f1'};display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:600;flex-shrink:0;`"
                >{{ (u.name||'?')[0].toUpperCase() }}</span>
                <span>{{ u.name }}</span>
                <el-text type="info" size="small">{{ u.email }}</el-text>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!assignInput" :loading="assigning" @click="submitAssign">确认指派</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { requirementsApi, iterationsApi, projectsApi, usersApi } from '@/api'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const { items: requirements, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange } = usePagination(
  async (p, ps) => {
    const res = await requirementsApi.list({ page: p, page_size: ps })
    return { items: res.data.items, total: res.data.total }
  }
)

const iterations = ref<any[]>([])
const projects = ref<any[]>([])
const users = ref<any[]>([])
const showAssignDialog = ref(false)
const assignTarget = ref<any>(null)
const assignInput = ref('')
const assigning = ref(false)

const filter = ref({ status: '', priority: '', search: '' })

const onFilterChange = () => fetchPage(1)

const displayedRequirements = computed(() => {
  let list = requirements.value
  if (filter.value.search.trim()) {
    const q = filter.value.search.trim().toLowerCase()
    list = list.filter((r: any) => r.title.toLowerCase().includes(q))
  }
  if (filter.value.status) list = list.filter((r: any) => r.status === filter.value.status)
  if (filter.value.priority) list = list.filter((r: any) => r.priority === filter.value.priority)
  return list
})

const priorityType = (p: string) => ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')
const statusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success', review_rejected: 'danger', completed: 'success',
}[s] || 'info')
const statusText = (s: string) => ({
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过', review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const getIterationName = (id: string) => iterations.value.find((i: any) => i.id === id)?.name || '—'
const userNameById = (id: string) => {
  if (!id) return null
  const u = users.value.find((u: any) => u.id === id)
  return u ? u.name : id.slice(0, 8) + '…'
}
const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

const fetchData = async () => {
  try {
    const [iterRes, projRes, usrRes] = await Promise.all([
      iterationsApi.list(), projectsApi.list(), usersApi.list(),
    ])
    users.value = usrRes.data
    iterations.value = iterRes.data.items
    projects.value = projRes.data.items
  } catch (e) { console.error(e) }
  fetchPage(1)
}

const openAssign = (row: any) => {
  assignTarget.value = row
  assignInput.value = row.assignee_id || ''
  showAssignDialog.value = true
}

const submitAssign = async () => {
  if (!assignTarget.value || !assignInput.value.trim()) return
  assigning.value = true
  try {
    const res = await requirementsApi.assign(assignTarget.value.id, assignInput.value.trim())
    const idx = requirements.value.findIndex(r => r.id === assignTarget.value.id)
    if (idx !== -1) requirements.value[idx] = res.data
    showAssignDialog.value = false
    ElMessage.success('指派成功')
  } catch (e) { console.error(e) }
  finally { assigning.value = false }
}

const deleteRequirement = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除此需求？', '提示', { type: 'warning' })
    await requirementsApi.delete(id)
    ElMessage.success('删除成功')
    fetchPage(page.value)
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

onMounted(fetchData)
</script>

<style scoped>
.requirements-page { width: 100%; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-left, .header-right { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; margin: 0; }
.assignee-badge {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 1px 6px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}
</style>
