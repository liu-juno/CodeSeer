<template>
  <div class="requirement-detail">
    <div class="back-row">
      <a @click.prevent="$router.back()" class="back-link" href="#">← 返回</a>
    </div>

    <div v-if="loading" class="card"><div class="text-muted">加载中...</div></div>

    <template v-else-if="requirement">
      <!-- Header card -->
      <div class="detail-header-card card">
        <div class="detail-title-row">
          <h1 class="detail-title">{{ requirement.title }}</h1>
          <div class="header-actions">
            <span :class="['status-badge', requirement.status]" style="font-size:13px;padding:5px 12px;">
              {{ statusText(requirement.status) }}
            </span>
            <!-- Transition buttons -->
            <template v-for="action in allowedTransitions" :key="action">
              <button
                class="btn btn-sm btn-primary"
                @click="action === 'assigned' ? (showAssignDialog = true) : doTransition(action)"
                :disabled="transitioning"
              >
                {{ transitionLabel(action) }}
              </button>
            </template>
          </div>
        </div>
        <div class="detail-meta-row">
          <div class="meta-item">
            <span class="meta-label">优先级</span>
            <span :class="['priority-badge', requirement.priority]">{{ requirement.priority }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">迭代</span>
            <span class="meta-value">{{ getIterationName(requirement.iteration_id) || '未关联' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">截止日期</span>
            <span class="meta-value">{{ requirement.due_date ? formatDate(requirement.due_date) : '未设置' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">创建时间</span>
            <span class="meta-value">{{ formatDate(requirement.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 开发阶段条 (5 phases) -->
      <div class="phases-bar card">
        <div class="phases-label">开发阶段</div>
        <div class="phases-track">
          <template v-for="(p, i) in phases" :key="p.id">
            <div
              :class="['phase-node', p.status]"
              :title="phaseLabel(p.phase) + (p.notes ? ' — ' + p.notes : '')"
              @click="cyclePhase(p)"
            >
              <div class="phase-icon">
                <span v-if="p.status === 'completed'">✓</span>
                <span v-else-if="p.status === 'in_progress'">◐</span>
                <span v-else>{{ i + 1 }}</span>
              </div>
              <div class="phase-name">{{ phaseLabel(p.phase) }}</div>
              <div class="phase-time">{{ p.completed_at ? formatDate(p.completed_at) : (p.started_at ? formatDate(p.started_at) : '') }}</div>
            </div>
            <div v-if="i < phases.length - 1" :class="['phase-connector', phases[i+1].status === 'completed' || p.status === 'completed' ? 'completed' : '']"></div>
          </template>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs-bar">
        <button v-for="tab in tabs" :key="tab.key"
          :class="['tab-btn', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key">
          {{ tab.label }}
          <span v-if="tab.key === 'tasks' && tasks.length" class="tab-count">{{ tasks.length }}</span>
          <span v-if="tab.key === 'tests' && testRecords.length" class="tab-count">{{ testRecords.length }}</span>
          <span v-if="tab.key === 'docs' && docs.length" class="tab-count">{{ docs.length }}</span>
        </button>
      </div>

      <!-- 基本信息 -->
      <div v-if="activeTab === 'info'" class="card tab-card">
        <div class="info-section">
          <div class="section-label">需求描述</div>
          <div class="section-content">{{ requirement.description || '暂无描述' }}</div>
        </div>
        <div class="info-section">
          <div class="section-label">验收标准</div>
          <div v-if="requirement.acceptance_criteria" class="criteria-display">
            <div v-for="(line, i) in criteriaLines" :key="i" class="criteria-line">
              <span class="criteria-dot">○</span>
              <span>{{ line }}</span>
            </div>
          </div>
          <div v-else class="text-muted text-medium">暂无验收标准</div>
        </div>
      </div>

      <!-- 任务 Tab -->
      <div v-if="activeTab === 'tasks'" class="card tab-card">
        <div v-if="tasksLoading" class="text-muted text-medium">加载中...</div>
        <div v-else-if="tasks.length === 0" class="ai-placeholder">
          <div class="ai-icon">⬡</div>
          <div class="ai-title">任务由 AI 自动同步</div>
          <div class="ai-desc">开发通过 Claude Code MCP 领取需求后，任务列表将自动同步至此</div>
        </div>
        <template v-else>
          <!-- Progress bar -->
          <div class="task-progress-row">
            <div class="task-progress-label">
              完成进度 {{ completedTasks }}/{{ tasks.length }}
            </div>
            <div class="task-progress-bar">
              <div class="task-progress-fill" :style="{ width: taskProgressPct + '%' }"></div>
            </div>
            <span class="task-progress-pct">{{ taskProgressPct }}%</span>
          </div>
          <table class="table" style="margin-top:12px">
            <thead>
              <tr>
                <th>#</th>
                <th>任务名称</th>
                <th>状态</th>
                <th>TDD 进度</th>
                <th>预估工时</th>
                <th>完成时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in tasks" :key="task.id">
                <td class="text-muted text-small">{{ task.order + 1 }}</td>
                <td style="font-weight:500">{{ task.title }}</td>
                <td>
                  <span :class="['task-status', task.status]">{{ taskStatusText(task.status) }}</span>
                </td>
                <td>
                  <div class="tdd-steps">
                    <span :class="['tdd-dot', task.tdd_red]" title="Red">R</span>
                    <span class="tdd-arrow">→</span>
                    <span :class="['tdd-dot', task.tdd_green]" title="Green">G</span>
                    <span class="tdd-arrow">→</span>
                    <span :class="['tdd-dot', task.tdd_refactor]" title="Refactor">F</span>
                  </div>
                </td>
                <td class="text-muted text-small">{{ task.estimated_hours ? task.estimated_hours + 'h' : '-' }}</td>
                <td class="text-muted text-small">{{ task.completed_at ? formatDate(task.completed_at) : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>

      <!-- 测试记录 Tab -->
      <div v-if="activeTab === 'tests'" class="card tab-card">
        <div v-if="testsLoading" class="text-muted text-medium">加载中...</div>
        <div v-else-if="testRecords.length === 0" class="ai-placeholder">
          <div class="ai-icon">⬡</div>
          <div class="ai-title">测试记录由 AI 自动上报</div>
          <div class="ai-desc">开发完成单元测试后，测试结果将通过 MCP 自动提交至此</div>
        </div>
        <template v-else>
          <!-- Summary -->
          <div class="test-summary">
            <div class="test-summary-item">
              <div class="ts-value">{{ testSummary.total }}</div>
              <div class="ts-label">总测试数</div>
            </div>
            <div class="test-summary-item green">
              <div class="ts-value">{{ testSummary.passed }}</div>
              <div class="ts-label">通过</div>
            </div>
            <div class="test-summary-item red">
              <div class="ts-value">{{ testSummary.failed }}</div>
              <div class="ts-label">失败</div>
            </div>
            <div class="test-summary-item">
              <div class="ts-value">{{ testSummary.coverage != null ? testSummary.coverage + '%' : '-' }}</div>
              <div class="ts-label">覆盖率</div>
            </div>
          </div>
          <table class="table" style="margin-top:12px">
            <thead>
              <tr>
                <th>关联任务</th>
                <th>类型</th>
                <th>总数</th>
                <th>通过</th>
                <th>失败</th>
                <th>覆盖率</th>
                <th>结果</th>
                <th>执行时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in testRecords" :key="rec.id">
                <td class="text-medium">{{ rec.task_title || '-' }}</td>
                <td class="text-muted text-small">{{ rec.test_type }}</td>
                <td class="text-small">{{ rec.total_count }}</td>
                <td class="text-small" style="color:#059669">{{ rec.passed_count }}</td>
                <td class="text-small" :style="rec.failed_count > 0 ? 'color:#dc2626' : ''">{{ rec.failed_count }}</td>
                <td class="text-small text-muted">{{ rec.coverage != null ? rec.coverage + '%' : '-' }}</td>
                <td>
                  <span :class="['test-result', rec.result]">{{ testResultText(rec.result) }}</span>
                </td>
                <td class="text-muted text-small">{{ formatDate(rec.executed_at) }}</td>
              </tr>
            </tbody>
          </table>
          <!-- Failed tests detail -->
          <template v-for="rec in testRecords.filter(r => r.failed_tests)" :key="rec.id + '-failed'">
            <div class="failed-tests-section">
              <div class="section-label" style="margin-bottom:8px">失败用例（{{ rec.task_title || '未知任务' }}）</div>
              <div class="failed-test-list">
                <div v-for="(ft, i) in parseFailedTests(rec.failed_tests)" :key="i" class="failed-test-item">
                  <span class="failed-test-name">{{ ft.name }}</span>
                  <span class="failed-test-msg text-muted text-small">{{ ft.message }}</span>
                </div>
              </div>
            </div>
          </template>
        </template>
      </div>
    </template>

    <div v-else class="card"><div class="text-muted">需求不存在</div></div>

    <!-- 文档 Tab -->
    <div v-if="activeTab === 'docs' && requirement" class="card tab-card">
      <div v-if="docs.length === 0" class="ai-placeholder">
        <div class="ai-icon">▤</div>
        <div class="ai-title">还没有文档</div>
        <div class="ai-desc">Claude Code 通过 MCP 提交设计文档后，将在这里展示</div>
      </div>
      <table v-else class="table" style="margin:-4px -4px">
        <thead>
          <tr><th>标题</th><th>类型</th><th>状态</th><th>版本</th><th>更新于</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in docs" :key="d.id">
            <td>
              <a href="javascript:;" class="link" @click="openDoc(d)">{{ d.title }}</a>
              <div v-if="d.summary" class="text-muted text-small" style="margin-top:2px;">{{ d.summary }}</div>
            </td>
            <td class="text-muted text-small">{{ d.document_type }}</td>
            <td><span :class="['status-badge', d.status]">{{ docStatusText(d.status) }}</span></td>
            <td class="text-muted text-small">v{{ d.version }}</td>
            <td class="text-muted text-small">{{ formatDate(d.updated_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 活动日志 Tab -->
    <div v-if="activeTab === 'history' && requirement" class="card tab-card">
      <div v-if="history.length === 0" class="ai-placeholder">
        <div class="ai-icon">◷</div>
        <div class="ai-title">暂无活动</div>
        <div class="ai-desc">状态变更、指派、文档操作都会记录在这里</div>
      </div>
      <div v-else class="timeline">
        <div v-for="h in history" :key="h.id" class="timeline-item">
          <div :class="['timeline-dot', actionClass(h.action)]">
            {{ actionIcon(h.action) }}
          </div>
          <div class="timeline-body">
            <div class="timeline-action">{{ actionText(h.action) }}</div>
            <div v-if="h.field_name" class="timeline-detail">
              <span class="text-muted">{{ h.field_name }}：</span>
              <span v-if="h.old_value" class="old-val">{{ h.old_value }}</span>
              <span v-if="h.old_value"> → </span>
              <span class="new-val">{{ h.new_value || '-' }}</span>
            </div>
            <div v-if="h.comment" class="timeline-comment text-muted text-small">{{ h.comment }}</div>
            <div class="timeline-meta text-muted text-small">
              {{ h.actor || 'system' }} · {{ formatDateTime(h.created_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Assign Dialog -->
  <div v-if="showAssignDialog" class="modal-overlay" @click.self="showAssignDialog = false">
    <div class="modal" style="width:420px;">
      <div class="modal-header">
        <h3>指派开发者</h3>
        <button class="modal-close" @click="showAssignDialog = false">✕</button>
      </div>
      <div class="modal-body">
        <div class="form-group" style="margin-bottom:0">
          <label class="form-label">开发者标识 <span class="required">*</span></label>
          <input
            v-model="assigneeInput"
            class="form-input"
            placeholder="输入开发者名称或 ID（如 dev@company.com）"
            autofocus
            @keyup.enter="assigneeInput.trim() && doAssign()"
          />
          <p class="form-hint">该标识将作为开发者通过 MCP 接入时的身份凭证</p>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="showAssignDialog = false">取消</button>
        <button class="btn btn-primary" :disabled="!assigneeInput || transitioning" @click="doAssign">
          {{ transitioning ? '指派中...' : '确认指派' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { requirementsApi, iterationsApi, tasksApi, testRecordsApi, documentsApi } from '@/api'

const route = useRoute()
const requirement = ref<any>(null)
const iterations = ref<any[]>([])
const tasks = ref<any[]>([])
const testRecords = ref<any[]>([])
const phases = ref<any[]>([])
const history = ref<any[]>([])
const docs = ref<any[]>([])
const loading = ref(false)
const tasksLoading = ref(false)
const testsLoading = ref(false)
const transitioning = ref(false)
const activeTab = ref('info')
const showAssignDialog = ref(false)
const assigneeInput = ref('')

const tabs = [
  { key: 'info', label: '基本信息' },
  { key: 'tasks', label: '任务' },
  { key: 'tests', label: '测试记录' },
  { key: 'docs', label: '文档' },
  { key: 'history', label: '活动日志' },
]

const TRANSITIONS: Record<string, string[]> = {
  draft:           ['pending_analysis'],
  pending_analysis:[],
  analyzed:        ['assigned'],
  assigned:        ['claimed', 'analyzed'],
  claimed:         ['in_progress'],
  in_progress:     ['pending_review'],
  pending_review:  ['review_approved', 'review_rejected'],
  review_approved: ['completed'],
  review_rejected: ['in_progress'],
  completed:       [],
}

const TRANSITION_LABELS: Record<string, string> = {
  pending_analysis: '提交分析',
  analyzed:        '标记已分析',
  assigned:        '指派',
  claimed:         '领取',
  in_progress:     '开始开发',
  pending_review:  '提交评审',
  review_approved: '评审通过',
  review_rejected: '评审驳回',
  completed:       '标记完成',
}

const allowedTransitions = computed(() => {
  if (!requirement.value) return []
  return TRANSITIONS[requirement.value.status] || []
})

const criteriaLines = computed(() =>
  (requirement.value?.acceptance_criteria || '').split('\n').filter((l: string) => l.trim())
)

const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const taskProgressPct = computed(() =>
  tasks.value.length ? Math.round((completedTasks.value / tasks.value.length) * 100) : 0
)

const testSummary = computed(() => {
  const total = testRecords.value.reduce((s, r) => s + r.total_count, 0)
  const passed = testRecords.value.reduce((s, r) => s + r.passed_count, 0)
  const failed = testRecords.value.reduce((s, r) => s + r.failed_count, 0)
  const coverages = testRecords.value.filter(r => r.coverage != null).map(r => r.coverage)
  const coverage = coverages.length ? Math.round(coverages.reduce((a, b) => a + b, 0) / coverages.length) : null
  return { total, passed, failed, coverage }
})

const statusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿', pending_analysis: '待分析', analyzed: '已分析',
    assigned: '已指派', claimed: '已领取', in_progress: '开发中',
    pending_review: '待评审', review_approved: '评审通过',
    review_rejected: '评审驳回', completed: '已完成',
  }
  return map[status] || status
}

const transitionLabel = (action: string) => TRANSITION_LABELS[action] || action

const taskStatusText = (s: string) => ({ pending: '待开始', in_progress: '进行中', completed: '已完成', blocked: '阻塞' }[s] || s)
const testResultText = (r: string) => ({ all_passed: '全部通过', failed: '失败', partial: '部分通过' }[r] || r)

const getIterationName = (id: string) => iterations.value.find((i: any) => i.id === id)?.name
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const formatDateTime = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const phaseLabel = (p: string) => ({
  clarification: '需求澄清', planning: '任务规划',
  execution: '任务执行', review: '代码审查', testing: '单元测试',
}[p] || p)

const actionIcon = (a: string) => ({
  created: '＋', updated: '✎', assigned: '☞', status_changed: '↻',
  document_submitted: '▤', document_archived: '✓', task_synced: '◆',
  test_submitted: '✓', iteration_released: '🚀',
}[a] || '◆')
const actionText = (a: string) => ({
  created: '创建', updated: '更新', assigned: '指派',
  status_changed: '状态变更', document_submitted: '提交文档',
  document_archived: '归档文档', task_synced: '同步任务',
  test_submitted: '提交测试', iteration_released: '发布迭代',
}[a] || a)
const actionClass = (a: string) => ({
  status_changed: 'green', assigned: 'blue', document_archived: 'green',
  iteration_released: 'purple', test_submitted: 'green', document_submitted: 'amber',
}[a] || 'gray')

const docStatusText = (s: string) => ({ draft: '草稿', archived: '已归档', deprecated: '已废弃' }[s] || s)

const PHASE_NEXT: Record<string, string> = {
  pending: 'in_progress', in_progress: 'completed', completed: 'pending',
}

const cyclePhase = async (p: any) => {
  const next = PHASE_NEXT[p.status]
  try {
    await requirementsApi.updatePhase(route.params.id as string, p.id, { status: next })
    fetchPhases()
    fetchHistory()
  } catch (e) { console.error(e) }
}

const openDoc = (d: any) => {
  // 简单弹出内容
  const w = window.open('', '_blank', 'width=720,height=640')
  if (w) {
    w.document.write(`<title>${d.title}</title><pre style="font-family:monospace; padding:24px; white-space:pre-wrap;">${(d.content || '').replace(/</g, '&lt;')}</pre>`)
  }
}

const parseFailedTests = (raw: string) => {
  try { return JSON.parse(raw) } catch { return [] }
}

const doTransition = async (action: string) => {
  transitioning.value = true
  try {
    const res = await requirementsApi.transition(route.params.id as string, action)
    requirement.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    transitioning.value = false
  }
}

const doAssign = async () => {
  if (!assigneeInput.value.trim()) return
  transitioning.value = true
  try {
    const res = await requirementsApi.assign(route.params.id as string, assigneeInput.value.trim())
    requirement.value = res.data
    showAssignDialog.value = false
    assigneeInput.value = ''
  } catch (e) {
    console.error(e)
  } finally {
    transitioning.value = false
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [reqRes, iterRes] = await Promise.all([
      requirementsApi.get(route.params.id as string),
      iterationsApi.list(),
    ])
    requirement.value = reqRes.data
    iterations.value = iterRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchTasks = async () => {
  tasksLoading.value = true
  try {
    const res = await tasksApi.list(route.params.id as string)
    tasks.value = res.data
  } catch (e) { console.error(e) }
  finally { tasksLoading.value = false }
}

const fetchTests = async () => {
  testsLoading.value = true
  try {
    const res = await testRecordsApi.list(route.params.id as string)
    testRecords.value = res.data
  } catch (e) { console.error(e) }
  finally { testsLoading.value = false }
}

const fetchPhases = async () => {
  try {
    const res = await requirementsApi.phases(route.params.id as string)
    phases.value = res.data
  } catch (e) { console.error(e) }
}

const fetchHistory = async () => {
  try {
    const res = await requirementsApi.history(route.params.id as string)
    history.value = res.data
  } catch (e) { console.error(e) }
}

const fetchDocs = async () => {
  try {
    const res = await documentsApi.list({ requirement_id: route.params.id })
    docs.value = res.data
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await fetchData()
  fetchTasks()
  fetchTests()
  fetchPhases()
  fetchHistory()
  fetchDocs()
})
</script>

<style scoped>
.back-row { margin-bottom: 16px; }

.back-link {
  color: #6b7280; text-decoration: none;
  font-size: 13.5px; font-weight: 500; transition: color 0.15s;
}
.back-link:hover { color: #6366f1; }

.detail-header-card {
  border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-bottom: none;
}

.detail-title-row {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px; margin-bottom: 16px;
}

.header-actions {
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}

.detail-title {
  font-size: 20px; font-weight: 700; color: #111827;
  letter-spacing: -0.3px; line-height: 1.3;
}

.detail-meta-row { display: flex; gap: 24px; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 6px; }
.meta-label { font-size: 12px; color: #9ca3af; font-weight: 500; }
.meta-value { font-size: 13px; color: #374151; font-weight: 500; }

.tabs-bar {
  display: flex; background: #fff;
  border: 1px solid #e5e7eb; border-top: none; border-bottom: none;
  padding: 0 20px; gap: 0;
}

.tab-btn {
  padding: 12px 16px; background: none; border: none;
  border-bottom: 2px solid transparent; cursor: pointer;
  color: #6b7280; font-size: 13.5px; font-weight: 500;
  transition: all 0.15s; display: flex; align-items: center; gap: 6px;
}
.tab-btn:hover { color: #374151; }
.tab-btn.active { color: #6366f1; border-bottom-color: #6366f1; }

.tab-count {
  background: #e0e7ff; color: #4338ca;
  font-size: 11px; font-weight: 600;
  padding: 1px 6px; border-radius: 10px;
}

.tab-card { border-top-left-radius: 0; border-top-right-radius: 0; }

.info-section { margin-bottom: 24px; }
.info-section:last-child { margin-bottom: 0; }
.section-label {
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.06em;
  color: #9ca3af; margin-bottom: 8px;
}
.section-content { font-size: 14px; color: #374151; line-height: 1.7; white-space: pre-wrap; }
.criteria-display { display: flex; flex-direction: column; gap: 8px; }
.criteria-line { display: flex; align-items: flex-start; gap: 8px; font-size: 14px; color: #374151; }
.criteria-dot { color: #6366f1; flex-shrink: 0; margin-top: 1px; }

/* Task progress */
.task-progress-row {
  display: flex; align-items: center; gap: 12px; margin-bottom: 4px;
}
.task-progress-label { font-size: 13px; color: #374151; font-weight: 500; white-space: nowrap; }
.task-progress-bar {
  flex: 1; height: 6px; background: #f0f1f5; border-radius: 3px; overflow: hidden;
}
.task-progress-fill {
  height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 3px; transition: width 0.3s;
}
.task-progress-pct { font-size: 13px; color: #6366f1; font-weight: 600; min-width: 36px; text-align: right; }

/* Task status */
.task-status {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 500; padding: 2px 8px; border-radius: 4px;
}
.task-status::before {
  content: ''; width: 5px; height: 5px; border-radius: 50%; background: currentColor; opacity: 0.7;
}
.task-status.pending    { background: #f3f4f6; color: #6b7280; }
.task-status.in_progress{ background: #fef9c3; color: #a16207; }
.task-status.completed  { background: #d1fae5; color: #065f46; }
.task-status.blocked    { background: #fee2e2; color: #991b1b; }

/* TDD */
.tdd-steps { display: flex; align-items: center; gap: 4px; }
.tdd-dot {
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700;
  background: #f3f4f6; color: #9ca3af;
}
.tdd-dot.completed { background: #d1fae5; color: #065f46; }
.tdd-dot.in_progress { background: #fef9c3; color: #a16207; }
.tdd-arrow { font-size: 10px; color: #d1d5db; }

/* Test summary */
.test-summary {
  display: flex; gap: 24px;
  background: #f9fafb; border-radius: 8px; padding: 16px 20px;
  border: 1px solid #f0f1f5; margin-bottom: 4px;
}
.test-summary-item { text-align: center; }
.test-summary-item.green .ts-value { color: #059669; }
.test-summary-item.red .ts-value { color: #dc2626; }
.ts-value { font-size: 22px; font-weight: 700; color: #111827; }
.ts-label { font-size: 12px; color: #6b7280; margin-top: 2px; }

/* Test result */
.test-result {
  font-size: 12px; font-weight: 500; padding: 2px 8px; border-radius: 4px;
}
.test-result.all_passed { background: #d1fae5; color: #065f46; }
.test-result.failed     { background: #fee2e2; color: #991b1b; }
.test-result.partial    { background: #fef9c3; color: #a16207; }

/* Failed tests */
.failed-tests-section { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f1f5; }
.failed-test-list { display: flex; flex-direction: column; gap: 8px; }
.failed-test-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 12px; background: #fff5f5; border-radius: 6px;
  border-left: 3px solid #fca5a5;
}
.failed-test-name { font-size: 13px; font-weight: 600; color: #991b1b; font-family: monospace; }
.failed-test-msg { font-size: 12px; margin-top: 2px; }

/* Phases */
.phases-bar {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 20px; margin-bottom: 0;
  border-top-left-radius: 0; border-top-right-radius: 0;
}
.phases-label {
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.06em;
  color: #9ca3af; flex-shrink: 0;
}
.phases-track {
  display: flex; align-items: center; gap: 0; flex: 1;
}
.phase-node {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  cursor: pointer; padding: 4px 8px;
  flex-shrink: 0; min-width: 80px;
  transition: opacity 0.1s;
}
.phase-node:hover { opacity: 0.7; }
.phase-icon {
  width: 28px; height: 28px; border-radius: 50%;
  background: #f3f4f6; color: #9ca3af;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  transition: all 0.2s;
}
.phase-name { font-size: 12px; font-weight: 500; color: #6b7280; }
.phase-time { font-size: 10px; color: #9ca3af; }
.phase-node.completed .phase-icon { background: #d1fae5; color: #065f46; }
.phase-node.completed .phase-name { color: #065f46; }
.phase-node.in_progress .phase-icon { background: #fef9c3; color: #a16207; animation: phase-pulse 1.5s infinite; }
.phase-node.in_progress .phase-name { color: #a16207; }
.phase-connector {
  flex: 1; height: 2px; background: #f0f1f5;
  min-width: 16px; transition: background 0.2s;
}
.phase-connector.completed { background: #10b981; }
@keyframes phase-pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }

/* Timeline */
.timeline { padding: 8px 0; }
.timeline-item {
  display: flex; gap: 12px;
  padding: 12px 0;
  position: relative;
}
.timeline-item:not(:last-child)::after {
  content: ''; position: absolute;
  left: 13px; top: 36px; bottom: -4px;
  width: 1px; background: #f0f1f5;
}
.timeline-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
  border: 2px solid white; box-shadow: 0 0 0 1px #e5e7eb;
}
.timeline-dot.green  { background: #d1fae5; color: #065f46; }
.timeline-dot.blue   { background: #dbeafe; color: #1e40af; }
.timeline-dot.purple { background: #ede9fe; color: #5b21b6; }
.timeline-dot.amber  { background: #fef9c3; color: #a16207; }
.timeline-dot.gray   { background: #f3f4f6; color: #6b7280; }
.timeline-body { flex: 1; min-width: 0; }
.timeline-action { font-size: 13.5px; font-weight: 600; color: #111827; }
.timeline-detail { font-size: 12.5px; color: #6b7280; margin-top: 2px; }
.timeline-detail .old-val { color: #dc2626; text-decoration: line-through; }
.timeline-detail .new-val { color: #059669; font-weight: 500; }
.timeline-comment { margin-top: 4px; }
.timeline-meta { margin-top: 4px; }

.ai-placeholder { text-align: center; padding: 40px 24px; }
.ai-icon { font-size: 32px; color: #8b5cf6; margin-bottom: 12px; opacity: 0.6; }
.ai-title { font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 6px; }
.ai-desc { font-size: 13px; color: #9ca3af; max-width: 380px; margin: 0 auto; line-height: 1.6; }
</style>
