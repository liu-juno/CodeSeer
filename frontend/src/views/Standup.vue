<template>
  <div class="standup-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">早会视图</h1>
        <p class="page-subtitle">按开发人员查看需求进度与阻塞情况</p>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <el-select v-model="selectedIteration" placeholder="全部迭代" style="width:200px" clearable>
          <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
        </el-select>
      </div>
    </div>

    <el-row :gutter="14" style="margin-bottom:20px;">
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon indigo">◇</div>
            <div>
              <div class="stat-value">{{ overview.total }}</div>
              <div class="stat-label">总需求</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon amber">↻</div>
            <div>
              <div class="stat-value">{{ overview.inProgress }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon green">✓</div>
            <div>
              <div class="stat-value">{{ overview.completed }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon purple">◈</div>
            <div>
              <div class="stat-value">{{ overview.unassigned }}</div>
              <div class="stat-label">待指派</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <el-card v-if="overdueReqs.length" shadow="never" style="margin-bottom:16px;">
      <template #header>
        <span style="color:#dc2626; font-weight:600;">🔥 延期提醒 ({{ overdueReqs.length }})</span>
      </template>
      <el-table :data="overdueReqs" stripe size="small">
        <el-table-column prop="title" label="需求标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click="$router.push(`/requirement/${row.id}`)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="assignee_id" label="负责人" width="120">
          <template #default="{ row }">
            <el-text type="info">{{ row.assignee_id ? row.assignee_id.slice(0, 8) : '未指派' }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止日期" width="120">
          <template #default="{ row }">
            <el-text>{{ formatDate(row.due_date) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="已延期" width="80">
          <template #default="{ row }">
            <el-tag type="danger" size="small">{{ daysOverdue(row.due_date) }} 天</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small" effect="plain">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="unassignedReqs.length" shadow="never" style="margin-bottom:16px;">
      <template #header>
        <span style="color:#d97706; font-weight:600;">⚠ 待指派需求 ({{ unassignedReqs.length }})</span>
      </template>
      <el-table :data="unassignedReqs" stripe size="small">
        <el-table-column prop="title" label="需求标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click="$router.push(`/requirement/${row.id}`)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small" effect="plain">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="iteration_id" label="迭代" width="120">
          <template #default="{ row }">
            <el-text type="info">{{ getIterationName(row.iteration_id) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div v-if="!loading">
      <el-empty v-if="developerGroups.length === 0" description="暂无已指派的需求" />

      <el-card v-for="dev in developerGroups" :key="dev.assigneeId" shadow="never" style="margin-bottom:16px; padding:0;">
        <template #header>
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="dev-avatar">{{ dev.assigneeId.slice(0, 2).toUpperCase() }}</div>
            <div style="flex:1;">
              <div style="font-weight:600; font-size:14px;">开发者 {{ dev.assigneeId.slice(0, 8) }}</div>
              <el-text type="info" class="text-small">进行中 {{ dev.inProgress }} 个 · 已完成 {{ dev.completed }} 个</el-text>
            </div>
            <div style="display:flex; align-items:center; gap:10px; width:180px;">
              <el-progress :percentage="dev.progressPct" :stroke-width="6" />
              <span style="font-weight:600; color:#6366f1; min-width:36px;">{{ dev.progressPct }}%</span>
            </div>
          </div>
        </template>

        <div class="req-list">
          <div v-for="req in dev.requirements" :key="req.id" class="req-row">
            <div class="req-row-left">
              <span :class="['req-status-dot', req.status]"></span>
              <el-link type="primary" underline="never" @click="$router.push(`/requirement/${req.id}`)">
                {{ req.title }}
              </el-link>
            </div>
            <div class="req-row-right">
              <el-tag :type="priorityType(req.priority)" size="small" effect="plain">{{ req.priority }}</el-tag>
              <el-tag :type="statusType(req.status)" size="small">{{ statusText(req.status) }}</el-tag>
              <el-text type="info" class="text-small">{{ getIterationName(req.iteration_id) }}</el-text>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { requirementsApi, iterationsApi } from '@/api'

const requirements = ref<any[]>([])
const iterations = ref<any[]>([])
const loading = ref(false)
const selectedIteration = ref('')

const filteredReqs = computed(() =>
  selectedIteration.value
    ? requirements.value.filter(r => r.iteration_id === selectedIteration.value)
    : requirements.value
)

const overview = computed(() => ({
  total: filteredReqs.value.length,
  inProgress: filteredReqs.value.filter(r => ['in_progress', 'pending_review'].includes(r.status)).length,
  completed: filteredReqs.value.filter(r => r.status === 'completed').length,
  unassigned: filteredReqs.value.filter(r => !r.assignee_id && r.status !== 'completed').length,
}))

const unassignedReqs = computed(() =>
  filteredReqs.value.filter(r => !r.assignee_id && !['completed', 'draft'].includes(r.status))
)

const today = computed(() => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
})

const overdueReqs = computed(() =>
  filteredReqs.value
    .filter(r => r.due_date && r.status !== 'completed' && new Date(r.due_date) < today.value)
    .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
)

const daysOverdue = (due: string) => {
  const dueDate = new Date(due)
  dueDate.setHours(0, 0, 0, 0)
  return Math.floor((today.value.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24))
}

const formatDate = (d: string) => d ? new Date(d).toISOString().slice(0, 10) : '-'

const developerGroups = computed(() => {
  const assigned = filteredReqs.value.filter(r => r.assignee_id)
  const groups: Record<string, any[]> = {}
  for (const req of assigned) {
    if (!groups[req.assignee_id]) groups[req.assignee_id] = []
    groups[req.assignee_id].push(req)
  }
  return Object.entries(groups).map(([assigneeId, reqs]) => {
    const completed = reqs.filter(r => r.status === 'completed').length
    const inProgress = reqs.filter(r => ['in_progress', 'pending_review'].includes(r.status)).length
    return {
      assigneeId,
      requirements: reqs,
      completed,
      inProgress,
      progressPct: reqs.length ? Math.round((completed / reqs.length) * 100) : 0,
    }
  })
})

const statusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success', review_rejected: 'danger', completed: 'success',
}[s] || 'info')
const priorityType = (p: string) => ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')

const statusText = (s: string) => ({
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const getIterationName = (id: string) => iterations.value.find((i: any) => i.id === id)?.name || '-'

const fetchData = async () => {
  loading.value = true
  try {
    const [reqRes, iterRes] = await Promise.all([requirementsApi.list(), iterationsApi.list()])
    requirements.value = reqRes.data.items
    iterations.value = iterRes.data.items
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; margin: 0; }
.page-subtitle { font-size: 13px; color: #969ba4; margin: 4px 0 0 0; }
.stat-value { font-size: 22px; font-weight: 700; color: #1f2329; line-height: 1; }
.stat-label { font-size: 12px; color: #969ba4; margin-top: 3px; }
.stat-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.stat-icon.indigo { background: rgba(99, 102, 241, 0.1); }
.stat-icon.amber { background: rgba(255, 154, 46, 0.1); }
.stat-icon.green { background: rgba(0, 168, 112, 0.1); }
.stat-icon.purple { background: rgba(139, 92, 246, 0.1); }
.dev-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.req-list { padding: 8px 0; }
.req-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; gap: 12px;
  border-bottom: 1px solid #f9fafb; transition: background 0.1s;
}
.req-row:last-child { border-bottom: none; }
.req-row:hover { background: #f9fafb; }
.req-row-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.req-row-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.req-status-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  background: #d1d5db;
}
.req-status-dot.in_progress { background: #f59e0b; }
.req-status-dot.pending_review { background: #ec4899; }
.req-status-dot.completed { background: #10b981; }
</style>
