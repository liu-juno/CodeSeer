<template>
  <div class="requirements-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">需求管理</h1>
        <el-text class="text-muted" style="margin-left:12px;">{{ total }} 条需求</el-text>
      </div>
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
        <el-button type="primary" @click="openWizard">
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

    <el-dialog v-model="showWizard" title="创建需求" width="600px" :close-on-click-modal="false">
      <el-steps :active="currentStep" finish-status="success" style="margin-bottom:24px;">
        <el-step v-for="(s, i) in steps" :key="i" :title="s" />
      </el-steps>

      <el-form :model="form" label-position="top">
        <div v-show="currentStep === 0">
          <el-form-item label="需求标题" required>
            <el-input v-model="form.title" placeholder="用一句话描述这个需求..." />
          </el-form-item>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
            <el-form-item label="所属项目" required>
              <el-select v-model="form.project_id" placeholder="选择项目" style="width:100%" @change="onProjectChange">
                <el-option v-for="proj in projects" :key="proj.id" :label="proj.name" :value="proj.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="关联迭代">
              <el-select v-model="form.iteration_id" placeholder="选择迭代" style="width:100%">
                <el-option v-for="iter in filteredIterations" :key="iter.id" :label="iter.name" :value="iter.id" />
              </el-select>
            </el-form-item>
          </div>
        </div>

        <div v-show="currentStep === 1">
          <el-form-item label="需求描述">
            <VditorEditor
              v-model="form.description"
              placeholder="请输入需求描述，支持 Markdown 格式"
              height="300px"
            />
          </el-form-item>
          <el-form-item label="验收标准">
            <div v-for="(item, idx) in form.criteriaList" :key="idx" style="display:flex; gap:8px; margin-bottom:8px;">
              <el-input v-model="form.criteriaList[idx]" :placeholder="`验收条件 ${idx + 1}`" style="flex:1;" />
              <el-button text type="danger" @click="removeCriteria(idx)">×</el-button>
            </div>
            <el-button text type="primary" @click="addCriteria">+ 添加验收标准</el-button>
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
            <div v-if="form.uploadedFiles.length" style="margin-top:12px;">
              <div v-for="(f, i) in form.uploadedFiles" :key="i" style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                <el-icon><Document /></el-icon>
                <span style="flex:1; font-size:13px;">{{ f.name }}</span>
                <span style="color:#909399; font-size:12px;">{{ (f.size / 1024).toFixed(1) }} KB</span>
                <el-button text type="danger" size="small" @click="removeFile(i)">×</el-button>
              </div>
            </div>
          </el-form-item>
        </div>

        <div v-show="currentStep === 2">
          <el-form-item label="优先级">
            <el-radio-group v-model="form.priority">
              <el-radio-button value="P0">P0 紧急</el-radio-button>
              <el-radio-button value="P1">P1 高</el-radio-button>
              <el-radio-button value="P2">P2 中</el-radio-button>
              <el-radio-button value="P3">P3 低</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="截止日期">
            <el-date-picker v-model="form.due_date" type="date" placeholder="选择日期" style="width:200px" value-format="YYYY-MM-DD" />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <el-button v-if="currentStep > 0" @click="currentStep--">上一步</el-button>
        <el-button v-if="currentStep < 2" type="primary" :disabled="!canNext" @click="currentStep++">下一步</el-button>
        <el-button v-if="currentStep === 2" type="primary" :loading="submitting" @click="submitRequirement">创建需求</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { requirementsApi, iterationsApi, projectsApi, usersApi, attachmentsApi } from '@/api'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'
import VditorEditor from '@/components/VditorEditor.vue'

const route = useRoute()

const { items: requirements, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange } = usePagination(
  async (p, ps) => {
    const res = await requirementsApi.list({ page: p, page_size: ps })
    return { items: res.data.items, total: res.data.total }
  }
)

const iterations = ref<any[]>([])
const projects = ref<any[]>([])
const users = ref<any[]>([])
const showWizard = ref(false)
const currentStep = ref(0)
const submitting = ref(false)
const showAssignDialog = ref(false)
const assignTarget = ref<any>(null)
const assignInput = ref('')
const assigning = ref(false)

const steps = ['基础信息', '需求内容', '设置']

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

const DESCRIPTION_TEMPLATE = `## 背景
[描述业务背景和用户痛点]

## 用户故事
作为 [用户角色]，我希望 [功能目标]，以便 [获得价值]。

## 功能说明
[详细描述功能逻辑和交互细节]`

const defaultForm = () => ({
  title: '', project_id: '', iteration_id: '', description: DESCRIPTION_TEMPLATE,
  criteriaList: [''], priority: 'P2', due_date: '', uploadedFiles: [] as File[],
})

const form = ref(defaultForm())

const filteredIterations = computed(() => {
  if (!form.value.project_id) return iterations.value
  return iterations.value.filter((i: any) => i.project_id === form.value.project_id)
})

const canNext = computed(() => {
  if (currentStep.value === 0) return form.value.title.trim() && form.value.project_id
  return true
})

const openWizard = () => { form.value = defaultForm(); currentStep.value = 0; showWizard.value = true }
const onProjectChange = () => { form.value.iteration_id = '' }
const addCriteria = () => { form.value.criteriaList.push('') }
const removeCriteria = (idx: number) => { form.value.criteriaList.splice(idx, 1); if (!form.value.criteriaList.length) form.value.criteriaList.push('') }

const uploadRef = ref()
const onFileChange = (file: any) => { form.value.uploadedFiles.push(file.raw) }
const removeFile = (index: number) => { form.value.uploadedFiles.splice(index, 1) }

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

    for (const file of form.value.uploadedFiles) {
      await attachmentsApi.upload(requirementId, file)
    }

    showWizard.value = false
    ElMessage.success('创建成功')
    fetchPage(page.value)
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
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
.requirements-page { max-width: 1200px; }
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
