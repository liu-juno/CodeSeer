<template>
  <div class="requirement-detail">
    <el-link underline="never" type="primary" @click="$router.back()" style="margin-bottom:16px; display:inline-block;">
      ← 返回
    </el-link>

    <div v-if="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else-if="requirement">
      <el-card shadow="never" style="margin-bottom:0;">
        <template #header>
          <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
            <h1 class="detail-title">{{ requirement.title }}</h1>
            <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
              <el-tag :type="statusType(requirement.status)">{{ statusText(requirement.status) }}</el-tag>
              <template v-for="action in allowedTransitions" :key="action">
                <el-button
                  size="small"
                  type="primary"
                  @click="action === 'assigned' ? (showAssignDialog = true) : doTransition(action)"
                  :loading="transitioning"
                >
                  {{ transitionLabel(action) }}
                </el-button>
              </template>
            </div>
          </div>
        </template>
        <div style="display:flex; gap:24px; flex-wrap:wrap;">
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="meta-label">优先级</span>
            <el-tag :type="priorityType(requirement.priority)" size="small" effect="plain">{{ requirement.priority }}</el-tag>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="meta-label">迭代</span>
            <span class="meta-value">{{ getIterationName(requirement.iteration_id) || '未关联' }}</span>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="meta-label">截止日期</span>
            <span class="meta-value">{{ requirement.due_date ? formatDate(requirement.due_date) : '未设置' }}</span>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="meta-label">创建时间</span>
            <span class="meta-value">{{ formatDate(requirement.created_at) }}</span>
          </div>
        </div>
      </el-card>

      <div class="phase-pipeline">
        <div
          v-for="(p, i) in phases"
          :key="p.id"
          :class="['phase-card', p.status]"
          @click="cyclePhase(p)"
        >
          <div class="phase-connector" v-if="i > 0" />
          <div class="phase-icon">{{ phaseIcon(p.phase) }}</div>
          <div class="phase-status-bar">
            <div :class="['phase-dot', p.status]" />
          </div>
          <div class="phase-name">{{ phaseLabel(p.phase) }}</div>
          <div class="phase-status-label">{{ phaseStatusLabel(p.status) }}</div>
        </div>
      </div>

      <el-tabs v-model="activeTab" style="margin-top:16px;">
        <el-tab-pane label="基本信息" name="info">
          <el-card shadow="never">
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
              <el-text v-else type="info">暂无验收标准</el-text>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane name="tasks">
          <template #label>
            任务 <el-badge :value="tasks.length" :hidden="!tasks.length" /></template>
          <el-card shadow="never">
            <div v-if="tasksLoading">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="tasks.length === 0" class="ai-placeholder">
              <div class="ai-icon">⬡</div>
              <div class="ai-title">任务由 AI 自动同步</div>
              <div class="ai-desc">开发通过 Claude Code MCP 领取需求后，任务列表将自动同步至此</div>
            </div>
            <template v-else>
              <div class="task-progress-row">
                <span class="task-progress-label">完成进度 {{ completedTasks }}/{{ tasks.length }}</span>
                <el-progress :percentage="taskProgressPct" :stroke-width="6" style="flex:1;" />
                <span class="task-progress-pct">{{ taskProgressPct }}%</span>
              </div>
              <el-table :data="tasks" stripe style="margin-top:12px;">
                <el-table-column type="index" width="50" />
                <el-table-column prop="title" label="任务名称" min-width="200" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="taskStatusType(row.status)" size="small">{{ taskStatusText(row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="TDD 进度" width="160">
                  <template #default="{ row }">
                    <div class="tdd-track">
                      <div class="tdd-step" :class="row.tdd_red">
                        <div class="tdd-circle">R</div>
                        <div class="tdd-label">红</div>
                      </div>
                      <div class="tdd-connector" :class="row.tdd_green !== 'pending' ? 'done' : ''" />
                      <div class="tdd-step" :class="row.tdd_green">
                        <div class="tdd-circle">G</div>
                        <div class="tdd-label">绿</div>
                      </div>
                      <div class="tdd-connector" :class="row.tdd_refactor !== 'pending' ? 'done' : ''" />
                      <div class="tdd-step" :class="row.tdd_refactor">
                        <div class="tdd-circle">F</div>
                        <div class="tdd-label">重构</div>
                      </div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="estimated_hours" label="预估工时" width="90">
                  <template #default="{ row }">
                    <el-text type="info">{{ row.estimated_hours ? row.estimated_hours + 'h' : '-' }}</el-text>
                  </template>
                </el-table-column>
                <el-table-column prop="actual_hours" label="实际工时" width="90">
                  <template #default="{ row }">
                    <el-text :type="row.actual_hours ? 'primary' : 'info'">{{ row.actual_hours ? row.actual_hours + 'h' : '-' }}</el-text>
                  </template>
                </el-table-column>
                <el-table-column prop="completed_at" label="完成时间" width="120">
                  <template #default="{ row }">
                    <el-text type="info">{{ row.completed_at ? formatDate(row.completed_at) : '-' }}</el-text>
                  </template>
                </el-table-column>
              </el-table>
            </template>
          </el-card>
        </el-tab-pane>

        <el-tab-pane name="tests">
          <template #label>
            测试记录 <el-badge :value="testRecords.length" :hidden="!testRecords.length" />
          </template>
          <el-card shadow="never">
            <div v-if="testsLoading">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="testRecords.length === 0" class="ai-placeholder">
              <div class="ai-icon">⬡</div>
              <div class="ai-title">测试记录由 AI 自动上报</div>
              <div class="ai-desc">开发完成单元测试后，测试结果将通过 MCP 自动提交至此</div>
            </div>
            <template v-else>
              <div class="test-summary">
                <div class="ts-card">
                  <div class="ts-icon indigo">▤</div>
                  <div>
                    <div class="ts-value">{{ testSummary.total }}</div>
                    <div class="ts-label">总测试数</div>
                  </div>
                </div>
                <div class="ts-card">
                  <div class="ts-icon green">✓</div>
                  <div>
                    <div class="ts-value green">{{ testSummary.passed }}</div>
                    <div class="ts-label">通过</div>
                  </div>
                </div>
                <div class="ts-card">
                  <div class="ts-icon red">✗</div>
                  <div>
                    <div class="ts-value red">{{ testSummary.failed }}</div>
                    <div class="ts-label">失败</div>
                  </div>
                </div>
                <div class="ts-card">
                  <div class="ts-icon purple">◉</div>
                  <div>
                    <div class="ts-value">{{ testSummary.coverage != null ? testSummary.coverage + '%' : '-' }}</div>
                    <div class="ts-label">覆盖率</div>
                  </div>
                </div>
              </div>
              <el-table :data="testRecords" stripe style="margin-top:12px;" row-key="id">
                <el-table-column type="expand">
                  <template #default="{ row }">
                    <div v-if="row.failed_tests" style="padding:12px 24px; background:#1a1a1a; border-radius:6px; margin:4px 16px;">
                      <div style="font-size:12px; color:#f87171; font-weight:600; margin-bottom:8px;">失败用例</div>
                      <div
                        v-for="(line, i) in row.failed_tests.split('\n').filter(Boolean)"
                        :key="i"
                        style="font-size:12px; color:#fca5a5; font-family:monospace; padding:2px 0;"
                      >✗ {{ line }}</div>
                    </div>
                    <div v-else style="padding:8px 24px; color:#6b7280; font-size:12px;">无失败用例详情</div>
                  </template>
                </el-table-column>
                <el-table-column prop="task_title" label="关联任务 / 阶段" min-width="150" />
                <el-table-column prop="test_type" label="类型" width="80" />
                <el-table-column prop="total_count" label="总数" width="60" />
                <el-table-column prop="passed_count" label="通过" width="60">
                  <template #default="{ row }"><span style="color:#059669">{{ row.passed_count }}</span></template>
                </el-table-column>
                <el-table-column prop="failed_count" label="失败" width="60">
                  <template #default="{ row }">
                    <span :style="row.failed_count > 0 ? 'color:#dc2626; font-weight:600' : ''">{{ row.failed_count }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="coverage" label="覆盖率" width="80">
                  <template #default="{ row }">
                    <el-text type="info">{{ row.coverage != null ? row.coverage + '%' : '-' }}</el-text>
                  </template>
                </el-table-column>
                <el-table-column prop="result" label="结果" width="90">
                  <template #default="{ row }">
                    <el-tag :type="testResultType(row.result)" size="small">{{ testResultText(row.result) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="executed_at" label="执行时间" width="120">
                  <template #default="{ row }">
                    <el-text type="info">{{ formatDate(row.executed_at) }}</el-text>
                  </template>
                </el-table-column>
              </el-table>
            </template>
          </el-card>
        </el-tab-pane>

        <el-tab-pane name="docs">
          <template #label>
            文档 <el-badge :value="docs.length" :hidden="!docs.length" />
          </template>
          <el-card shadow="never">
            <div v-if="docs.length === 0" class="ai-placeholder">
              <div class="ai-icon">▤</div>
              <div class="ai-title">还没有文档</div>
              <div class="ai-desc">Claude Code 通过 MCP 提交设计文档后，将在这里展示</div>
            </div>
            <el-table v-else :data="docs" stripe>
              <el-table-column prop="title" label="标题" min-width="180">
                <template #default="{ row }">
                  <el-link type="primary" underline="never" @click="openDoc(row)">{{ row.title }}</el-link>
                  <div v-if="row.summary" class="text-muted text-small" style="margin-top:2px;">{{ row.summary }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="document_type" label="类型" width="70" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag size="small" :type="docStatusTagType(row.status)">{{ docStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="所属模块" width="160">
                <template #default="{ row }">
                  <el-select
                    v-if="row.status === 'draft'"
                    :model-value="row.module_id"
                    size="small"
                    placeholder="挂载模块"
                    clearable
                    style="width:100%;"
                    @change="(val: string) => assignModule(row, val)"
                  >
                    <el-option v-for="m in flatModules" :key="m.id" :label="m.label" :value="m.id" />
                  </el-select>
                  <el-text v-else type="info" size="small">{{ moduleNameById(row.module_id) || '—' }}</el-text>
                </template>
              </el-table-column>
              <el-table-column prop="version" label="版本" width="55" />
              <el-table-column prop="updated_at" label="更新于" width="110">
                <template #default="{ row }">
                  <el-text type="info">{{ formatDate(row.updated_at) }}</el-text>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="right">
                <template #default="{ row }">
                  <el-button
                    v-if="row.status === 'draft'"
                    size="small"
                    text
                    type="primary"
                    :loading="archivingId === row.id"
                    @click="archiveDoc(row)"
                  >归档</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane name="attachments">
          <template #label>
            附件 <el-badge :value="attachments.length" :hidden="!attachments.length" /></template>
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

        <el-tab-pane name="history" label="活动日志">
          <el-card shadow="never">
            <div v-if="history.length === 0" class="ai-placeholder">
              <div class="ai-icon">◷</div>
              <div class="ai-title">暂无活动</div>
              <div class="ai-desc">状态变更、指派、文档操作都会记录在这里</div>
            </div>
            <el-timeline v-else>
              <el-timeline-item v-for="h in history" :key="h.id" :type="actionClass(h.action)" hollow>
                <div class="timeline-action">{{ actionText(h.action) }}</div>
                <div v-if="h.field_name" class="timeline-detail">
                  <el-text type="info">{{ h.field_name }}：</el-text>
                  <span v-if="h.old_value" class="old-val">{{ h.old_value }}</span>
                  <span v-if="h.old_value"> → </span>
                  <span class="new-val">{{ h.new_value || '-' }}</span>
                </div>
                <div v-if="h.comment" class="timeline-comment text-muted text-small">{{ h.comment }}</div>
                <el-text type="info" class="text-small">{{ h.actor || 'system' }} · {{ formatDateTime(h.created_at) }}</el-text>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </template>

    <el-dialog v-model="showAssignDialog" title="指派开发者" width="420px">
      <el-form label-position="top">
        <el-form-item label="选择开发人员">
          <el-select v-model="assigneeInput" placeholder="请选择开发人员" style="width:100%" filterable>
            <el-option v-for="u in allUsers" :key="u.id" :value="u.id" :label="u.name">
              <div style="display:flex; align-items:center; gap:8px;">
                <span :style="`width:26px;height:26px;border-radius:50%;background:${u.avatar_color||'#6366f1'};display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:600;flex-shrink:0;`">{{ (u.name||'?')[0].toUpperCase() }}</span>
                <span>{{ u.name }}</span>
                <el-text type="info" size="small">{{ u.email }}</el-text>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!assigneeInput" :loading="transitioning" @click="doAssign">确认指派</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { requirementsApi, iterationsApi, tasksApi, testRecordsApi, documentsApi, modulesApi, usersApi, attachmentsApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const requirement = ref<any>(null)
const iterations = ref<any[]>([])
const allUsers = ref<any[]>([])
const tasks = ref<any[]>([])
const testRecords = ref<any[]>([])
const phases = ref<any[]>([])
const history = ref<any[]>([])
const docs = ref<any[]>([])
const modules = ref<any[]>([])
const attachments = ref<any[]>([])
const archivingId = ref<string | null>(null)
const loading = ref(false)
const tasksLoading = ref(false)
const testsLoading = ref(false)
const transitioning = ref(false)
const activeTab = ref('info')
const showAssignDialog = ref(false)
const assigneeInput = ref('')

const TRANSITIONS: Record<string, string[]> = {
  draft: ['assigned'],
  assigned: ['in_progress'],
  in_progress: ['pending_review'],
  pending_review: ['review_approved', 'review_rejected'],
  review_approved: ['completed'],
  review_rejected: ['in_progress'],
  completed: [],
}

const TRANSITION_LABELS: Record<string, string> = {
  assigned: '指派', in_progress: '开始开发', pending_review: '提交评审',
  review_approved: '评审通过', review_rejected: '评审驳回', completed: '标记完成',
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

const activePhaseIndex = computed(() => {
  const completedPhases = phases.value.filter(p => p.status === 'completed').length
  const inProgressIndex = phases.value.findIndex(p => p.status === 'in_progress')
  return inProgressIndex >= 0 ? inProgressIndex : completedPhases
})

const statusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success', review_rejected: 'danger', completed: 'success',
}[s] || 'info')
const priorityType = (p: string) => ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')
const taskStatusType = (s: string) => ({ pending: 'info', in_progress: 'warning', completed: 'success', blocked: 'danger' }[s] || 'info')
const testResultType = (r: string) => ({ all_passed: 'success', failed: 'danger', partial: 'warning' }[r] || 'info')

const statusText = (status: string) => ({
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[status] || status)

const transitionLabel = (action: string) => TRANSITION_LABELS[action] || action
const taskStatusText = (s: string) => ({ pending: '待开始', in_progress: '进行中', completed: '已完成', blocked: '阻塞' }[s] || s)
const testResultText = (r: string) => ({ all_passed: '全部通过', failed: '失败', partial: '部分通过' }[r] || r)

const getIterationName = (id: string) => iterations.value.find((i: any) => i.id === id)?.name
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const formatDateTime = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const phaseLabel = (p: string) => ({
  clarification: '需求澄清', planning: '任务规划',
  execution: '任务执行', testing: '单元测试', review: '代码审查',
}[p] || p)

const phaseIcon = (p: string) => ({
  clarification: '✎', planning: '☰', execution: '▶', testing: '✓', review: '⌘',
}[p] || '○')

const phaseStatusLabel = (s: string) => ({
  pending: '待开始', in_progress: '进行中', completed: '已完成',
}[s] || s)

const actionText = (a: string) => ({
  created: '创建', updated: '更新', assigned: '指派',
  status_changed: '状态变更', document_submitted: '提交文档',
  document_archived: '归档文档', task_synced: '同步任务',
  test_submitted: '提交测试', iteration_released: '发布迭代',
}[a] || a)
const actionClass = (a: string) => ({
  status_changed: 'success', assigned: 'primary', document_archived: 'success',
  iteration_released: 'warning', test_submitted: 'success', document_submitted: 'warning',
}[a] || 'info')

const docStatusText = (s: string) => ({ draft: '草稿', archived: '已归档', deprecated: '已废弃' }[s] || s)
const docStatusTagType = (s: string) => ({ draft: '', archived: 'success', deprecated: 'info' }[s] || '') as any

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
  const w = window.open('', '_blank', 'width=720,height=640')
  if (w) {
    w.document.write(`<title>${d.title}</title><pre style="font-family:monospace; padding:24px; white-space:pre-wrap;">${(d.content || '').replace(/</g, '&lt;')}</pre>`)
  }
}

const doTransition = async (action: string) => {
  transitioning.value = true
  try {
    const res = await requirementsApi.transition(route.params.id as string, action)
    requirement.value = res.data
  } catch (e) { console.error(e) }
  finally { transitioning.value = false }
}

const doAssign = async () => {
  if (!assigneeInput.value.trim()) return
  transitioning.value = true
  try {
    const res = await requirementsApi.assign(route.params.id as string, assigneeInput.value.trim())
    requirement.value = res.data
    showAssignDialog.value = false
    assigneeInput.value = ''
    ElMessage.success('指派成功')
  } catch (e) { console.error(e) }
  finally { transitioning.value = false }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [reqRes, iterRes] = await Promise.all([
      requirementsApi.get(route.params.id as string),
      iterationsApi.list(),
    ])
    requirement.value = reqRes.data
    iterations.value = iterRes.data.items
  } catch (e) { console.error(e) }
  finally { loading.value = false }
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

const fetchUsers = async () => {
  try {
    const res = await usersApi.list()
    allUsers.value = res.data
  } catch (e) { console.error(e) }
}

const flatModules = computed(() => {
  const out: { id: string; label: string }[] = []
  const walk = (list: any[], depth: number) => {
    for (const m of list) {
      out.push({ id: m.id, label: ' '.repeat(depth * 2) + m.name })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(modules.value, 0)
  return out
})

const moduleNameById = (id: string | null) => {
  if (!id) return null
  return flatModules.value.find(m => m.id === id)?.label?.trim() || null
}

const assignModule = async (doc: any, moduleId: string | null) => {
  try {
    await documentsApi.update(doc.id, { module_id: moduleId || null })
    doc.module_id = moduleId || null
    ElMessage.success(moduleId ? '已挂载模块' : '已取消挂载')
  } catch (e) { console.error(e) }
}

const archiveDoc = async (doc: any) => {
  archivingId.value = doc.id
  try {
    await documentsApi.archive(doc.id)
    ElMessage.success('归档成功')
    fetchDocs()
  } catch (e) {
    ElMessage.error('归档失败')
    console.error(e)
  } finally {
    archivingId.value = null
  }
}

const fetchDocs = async () => {
  try {
    const res = await documentsApi.list({ requirement_id: route.params.id })
    docs.value = res.data
  } catch (e) { console.error(e) }
}

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

const fetchModules = async () => {
  try {
    const res = await modulesApi.list()
    modules.value = res.data
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await fetchData()
  fetchTasks()
  fetchTests()
  fetchPhases()
  fetchHistory()
  fetchDocs()
  fetchModules()
  fetchUsers()
  fetchAttachments()
})
</script>

<style scoped>
.detail-title { font-size: 20px; font-weight: 700; color: #1f2329; letter-spacing: -0.3px; line-height: 1.3; margin: 0; }
.meta-label { font-size: 12px; color: #9ca3af; font-weight: 500; }
.meta-value { font-size: 13px; color: #374151; font-weight: 500; }
.task-progress-row { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.task-progress-label { font-size: 13px; color: #374151; font-weight: 500; white-space: nowrap; }
.task-progress-pct { font-size: 13px; color: #6366f1; font-weight: 600; min-width: 36px; text-align: right; }
.tdd-track {
  display: flex;
  align-items: center;
  gap: 0;
}
.tdd-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.tdd-circle {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  background: #f3f4f6;
  color: #9ca3af;
  border: 2px solid transparent;
  transition: all 0.2s;
}
.tdd-step.completed .tdd-circle {
  background: #d1fae5;
  color: #065f46;
  border-color: #6ee7b7;
}
.tdd-step.in_progress .tdd-circle {
  background: #eff6ff;
  color: #2d5bff;
  border-color: #93c5fd;
  animation: tddPulse 1.2s infinite;
}
@keyframes tddPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(45, 91, 255, 0.25); }
  50% { box-shadow: 0 0 0 4px rgba(45, 91, 255, 0); }
}
.tdd-label {
  font-size: 10px;
  color: #9ca3af;
  font-weight: 500;
}
.tdd-step.completed .tdd-label { color: #059669; }
.tdd-step.in_progress .tdd-label { color: #2d5bff; }
.tdd-connector {
  flex: 1;
  height: 2px;
  background: #e5e7eb;
  margin: 0 2px;
  margin-bottom: 14px;
  min-width: 16px;
}
.tdd-connector.done { background: #10b981; }
.test-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}
.ts-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f9fafb;
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid #f0f1f5;
}
.ts-icon {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.ts-icon.indigo { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
.ts-icon.green { background: rgba(0, 168, 112, 0.1); color: #059669; }
.ts-icon.red { background: rgba(239, 68, 68, 0.1); color: #dc2626; }
.ts-icon.purple { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.ts-value { font-size: 22px; font-weight: 700; color: #111827; line-height: 1; }
.ts-value.green { color: #059669; }
.ts-value.red { color: #dc2626; }
.ts-label { font-size: 12px; color: #6b7280; margin-top: 2px; }
.ai-placeholder { text-align: center; padding: 40px 24px; }
.ai-icon { font-size: 32px; color: #8b5cf6; margin-bottom: 12px; opacity: 0.6; }
.ai-title { font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 6px; }
.ai-desc { font-size: 13px; color: #9ca3af; max-width: 380px; margin: 0 auto; line-height: 1.6; }
.info-section { margin-bottom: 24px; }
.info-section:last-child { margin-bottom: 0; }
.section-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #9ca3af; margin-bottom: 8px; }
.section-content { font-size: 14px; color: #374151; line-height: 1.7; white-space: pre-wrap; }
.criteria-display { display: flex; flex-direction: column; gap: 8px; }
.criteria-line { display: flex; align-items: flex-start; gap: 8px; font-size: 14px; color: #374151; }
.criteria-dot { color: #6366f1; flex-shrink: 0; margin-top: 1px; }
.timeline-action { font-size: 13.5px; font-weight: 600; color: #111827; }
.timeline-detail { font-size: 12.5px; color: #6b7280; margin-top: 2px; }
.timeline-comment { margin-top: 4px; }
.old-val { color: #dc2626; text-decoration: line-through; }
.new-val { color: #059669; font-weight: 500; }

/* ─── Phase Pipeline ─────────────────────────────────── */
.phase-pipeline {
  display: flex;
  align-items: stretch;
  gap: 0;
  background: #ffffff;
  border-radius: 0 0 12px 12px;
  padding: 20px 24px;
  border-top: 1px solid #e8e9eb;
  overflow-x: auto;
}

.phase-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 90px;
  cursor: pointer;
  padding: 12px 8px 14px;
  border-radius: 10px;
  transition: background 0.15s;
}

.phase-card:hover {
  background: #f5f7ff;
}

.phase-card:last-child {
  min-width: 80px;
}

.phase-connector {
  position: absolute;
  top: 28px;
  left: -50%;
  width: 100%;
  height: 2px;
  background: #e5e7eb;
  z-index: 0;
}

.phase-card.completed .phase-connector {
  background: #10b981;
}

.phase-card.in_progress .phase-connector {
  background: linear-gradient(to right, #10b981 50%, #e5e7eb 50%);
}

.phase-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: #f3f4f6;
  color: #9ca3af;
  transition: all 0.2s;
  position: relative;
  z-index: 1;
}

.phase-card.completed .phase-icon {
  background: #d1fae5;
  color: #065f46;
}

.phase-card.in_progress .phase-icon {
  background: #eff6ff;
  color: #2d5bff;
  box-shadow: 0 0 0 3px rgba(45, 91, 255, 0.15);
}

.phase-card.pending .phase-icon {
  background: #f9fafb;
  color: #9ca3af;
  border: 1px solid #e5e7eb;
}

.phase-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
}

.phase-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}

.phase-dot.completed { background: #10b981; }
.phase-dot.in_progress { background: #2d5bff; animation: phasePulse 1.5s infinite; }

@keyframes phasePulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(45, 91, 255, 0.4); }
  50% { box-shadow: 0 0 0 4px rgba(45, 91, 255, 0); }
}

.phase-name {
  font-size: 12.5px;
  font-weight: 600;
  color: #374151;
  text-align: center;
  white-space: nowrap;
}

.phase-card.completed .phase-name { color: #059669; }
.phase-card.in_progress .phase-name { color: #2d5bff; }

.phase-status-label {
  font-size: 11px;
  color: #9ca3af;
  text-align: center;
}

.phase-card.completed .phase-status-label { color: #059669; }
.phase-card.in_progress .phase-status-label { color: #2d5bff; }
</style>
