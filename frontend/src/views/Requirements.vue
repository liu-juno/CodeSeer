<template>
  <div class="requirements-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">需求管理</h1>
        <p class="page-subtitle">管理产品需求，追踪开发全流程</p>
      </div>
      <button class="btn btn-primary" @click="openWizard">
        <span>＋</span> 创建需求
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-bar mb-16">
      <div class="search-wrap">
        <span class="search-icon">⌕</span>
        <input
          v-model="filter.search"
          class="form-input search-input"
          placeholder="搜索需求标题..."
          style="padding-left:32px; width:220px;"
        />
      </div>
      <select v-model="filter.status" class="form-input" style="width:140px">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="pending_analysis">待分析</option>
        <option value="analyzed">已分析</option>
        <option value="assigned">已指派</option>
        <option value="claimed">已领取</option>
        <option value="in_progress">开发中</option>
        <option value="pending_review">待评审</option>
        <option value="review_approved">评审通过</option>
        <option value="review_rejected">评审驳回</option>
        <option value="completed">已完成</option>
      </select>
      <select v-model="filter.priority" class="form-input" style="width:120px">
        <option value="">全部优先级</option>
        <option value="P0">P0 紧急</option>
        <option value="P1">P1 高</option>
        <option value="P2">P2 中</option>
        <option value="P3">P3 低</option>
      </select>
      <select v-model="filter.iterationId" class="form-input" style="width:180px">
        <option value="">全部迭代</option>
        <option v-for="iter in iterations" :key="iter.id" :value="iter.id">
          {{ iter.name }}
        </option>
      </select>
      <span class="filter-count text-muted text-small">{{ displayedRequirements.length }} 条</span>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state">
        <div class="empty-state-text text-muted">加载中...</div>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>需求标题</th>
            <th>优先级</th>
            <th>迭代</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="req in displayedRequirements" :key="req.id">
            <td>
              <router-link :to="`/requirements/${req.id}`" class="link">
                {{ req.title }}
              </router-link>
            </td>
            <td>
              <span :class="['priority-badge', req.priority]">{{ req.priority }}</span>
            </td>
            <td class="text-muted text-medium">{{ getIterationName(req.iteration_id) }}</td>
            <td>
              <span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span>
            </td>
            <td class="text-muted text-small">{{ formatDate(req.created_at) }}</td>
          </tr>
          <tr v-if="displayedRequirements.length === 0">
            <td colspan="5">
              <div class="empty-state">
                <div class="empty-state-icon">◇</div>
                <div class="empty-state-text">暂无需求，点击「创建需求」开始</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Wizard Modal ─────────────────────────────────── -->
    <div v-if="showWizard" class="modal-overlay" @click.self="closeWizard">
      <div class="modal" style="width:600px;">
        <div class="modal-header">
          <h3>创建需求</h3>
          <button class="modal-close" @click="closeWizard">✕</button>
        </div>

        <div class="modal-body">
          <!-- Step indicator -->
          <div class="wizard-steps">
            <div v-for="(s, i) in steps" :key="i"
                 :class="['wizard-step', { active: currentStep === i, completed: currentStep > i }]">
              <div class="step-circle">
                <span v-if="currentStep > i">✓</span>
                <span v-else>{{ i + 1 }}</span>
              </div>
              <span class="step-label">{{ s }}</span>
            </div>
          </div>

          <!-- Step 1: 基础信息 -->
          <div v-if="currentStep === 0">
            <div class="form-group">
              <label class="form-label">需求标题 <span class="required">*</span></label>
              <input
                v-model="form.title"
                type="text"
                class="form-input"
                placeholder="用一句话描述这个需求..."
                autofocus
              />
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">所属项目 <span class="required">*</span></label>
                <select v-model="form.project_id" class="form-input" @change="onProjectChange">
                  <option value="">选择项目</option>
                  <option v-for="proj in projects" :key="proj.id" :value="proj.id">
                    {{ proj.name }}
                  </option>
                </select>
              </div>
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">关联迭代</label>
                <select v-model="form.iteration_id" class="form-input">
                  <option value="">选择迭代</option>
                  <option v-for="iter in filteredIterations" :key="iter.id" :value="iter.id">
                    {{ iter.name }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Step 2: 需求内容 -->
          <div v-if="currentStep === 1">
            <div class="form-group">
              <label class="form-label">需求描述</label>
              <textarea
                v-model="form.description"
                class="form-input"
                style="min-height:110px"
                placeholder="As a [用户角色], I want [目标], so that [价值/原因]"
              ></textarea>
              <p class="form-hint">建议使用 User Story 格式填写</p>
            </div>
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">验收标准</label>
              <div class="criteria-list">
                <div v-for="(item, idx) in form.criteriaList" :key="idx" class="criteria-item">
                  <input
                    v-model="form.criteriaList[idx]"
                    type="text"
                    class="form-input"
                    :placeholder="`验收条件 ${idx + 1}`"
                  />
                  <button class="criteria-remove" @click="removeCriteria(idx)">×</button>
                </div>
              </div>
              <button class="btn-add-criteria" @click="addCriteria">
                <span>＋</span> 添加验收标准
              </button>
            </div>
          </div>

          <!-- Step 3: 设置与提交 -->
          <div v-if="currentStep === 2">
            <div class="form-group">
              <label class="form-label">优先级</label>
              <div class="priority-selector">
                <div
                  v-for="p in priorities"
                  :key="p.value"
                  :class="['priority-card', p.cls, { selected: form.priority === p.value }]"
                  @click="form.priority = p.value"
                >
                  <div class="p-label">{{ p.value }}</div>
                  <div class="p-desc">{{ p.label }}</div>
                </div>
              </div>
            </div>
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">截止日期 <span style="font-weight:400; color:#9ca3af;">（选填）</span></label>
              <input v-model="form.due_date" type="date" class="form-input" style="width:200px" />
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button v-if="currentStep > 0" class="btn btn-secondary" @click="currentStep--">
            ← 上一步
          </button>
          <button class="btn btn-secondary" @click="closeWizard" style="margin-right:auto;" v-if="currentStep === 0">
            取消
          </button>
          <button v-if="currentStep < 2" class="btn btn-primary" :disabled="!canNext" @click="nextStep">
            下一步 →
          </button>
          <button v-if="currentStep === 2" class="btn btn-primary" :disabled="submitting" @click="submitRequirement">
            {{ submitting ? '创建中...' : '✓ 创建需求' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { requirementsApi, iterationsApi, projectsApi } from '@/api'

const requirements = ref<any[]>([])
const iterations = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const showWizard = ref(false)
const currentStep = ref(0)
const submitting = ref(false)

const steps = ['基础信息', '需求内容', '设置']

const priorities = [
  { value: 'P0', label: '紧急', cls: 'p0' },
  { value: 'P1', label: '高', cls: 'p1' },
  { value: 'P2', label: '中', cls: 'p2' },
  { value: 'P3', label: '低', cls: 'p3' },
]

const filter = ref({ iterationId: '', status: '', priority: '', search: '' })

const displayedRequirements = computed(() => {
  let list = requirements.value
  if (filter.value.search.trim()) {
    const q = filter.value.search.trim().toLowerCase()
    list = list.filter((r: any) => r.title.toLowerCase().includes(q))
  }
  if (filter.value.status) list = list.filter((r: any) => r.status === filter.value.status)
  if (filter.value.priority) list = list.filter((r: any) => r.priority === filter.value.priority)
  if (filter.value.iterationId) list = list.filter((r: any) => r.iteration_id === filter.value.iterationId)
  return list
})

const defaultForm = () => ({
  title: '',
  project_id: '',
  iteration_id: '',
  description: '',
  criteriaList: [''],
  priority: 'P2',
  due_date: '',
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

const openWizard = () => {
  form.value = defaultForm()
  currentStep.value = 0
  showWizard.value = true
}

const closeWizard = () => {
  showWizard.value = false
}

const nextStep = () => {
  if (currentStep.value < 2) currentStep.value++
}

const onProjectChange = () => {
  form.value.iteration_id = ''
}

const addCriteria = () => {
  form.value.criteriaList.push('')
}

const removeCriteria = (idx: number) => {
  form.value.criteriaList.splice(idx, 1)
  if (form.value.criteriaList.length === 0) form.value.criteriaList.push('')
}

const statusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿', pending_analysis: '待分析', analyzed: '已分析',
    assigned: '已指派', claimed: '已领取', in_progress: '开发中',
    pending_review: '待评审', review_approved: '评审通过',
    review_rejected: '评审驳回', completed: '已完成',
  }
  return map[status] || status
}

const getIterationName = (iterationId: string) => {
  const it = iterations.value.find((i: any) => i.id === iterationId)
  return it?.name || '-'
}

const formatDate = (date: string) => new Date(date).toLocaleDateString('zh-CN')

const fetchData = async () => {
  loading.value = true
  try {
    const [reqRes, iterRes, projRes] = await Promise.all([
      requirementsApi.list(),
      iterationsApi.list(),
      projectsApi.list(),
    ])
    requirements.value = reqRes.data
    iterations.value = iterRes.data
    projects.value = projRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const submitRequirement = async () => {
  submitting.value = true
  try {
    const criteria = form.value.criteriaList.filter(c => c.trim()).join('\n')
    await requirementsApi.create({
      title: form.value.title,
      project_id: form.value.project_id,
      iteration_id: form.value.iteration_id || null,
      description: form.value.description,
      acceptance_criteria: criteria,
      priority: form.value.priority,
      due_date: form.value.due_date || null,
    })
    closeWizard()
    fetchData()
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.filters-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: #9ca3af;
  font-size: 15px;
  pointer-events: none;
  z-index: 1;
}

.filter-count {
  margin-left: 4px;
  white-space: nowrap;
}
</style>
