<template>
  <div class="standup-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">早会视图</h1>
        <p class="page-subtitle">按开发人员查看需求进度与阻塞情况</p>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <select v-model="selectedIteration" class="form-input" style="width:200px">
          <option value="">全部迭代</option>
          <option v-for="it in iterations" :key="it.id" :value="it.id">{{ it.name }}</option>
        </select>
      </div>
    </div>

    <!-- Overview stats -->
    <div class="stats-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-icon indigo">◇</div>
        <div class="stat-body">
          <div class="stat-value">{{ overview.total }}</div>
          <div class="stat-label">总需求</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon amber">↻</div>
        <div class="stat-body">
          <div class="stat-value">{{ overview.inProgress }}</div>
          <div class="stat-label">进行中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">✓</div>
        <div class="stat-body">
          <div class="stat-value">{{ overview.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">◈</div>
        <div class="stat-body">
          <div class="stat-value">{{ overview.unassigned }}</div>
          <div class="stat-label">待指派</div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="card"><div class="text-muted">加载中...</div></div>

    <!-- Unassigned requirements -->
    <div v-if="overdueReqs.length" class="card mb-16">
      <div class="card-title" style="color:#dc2626;">🔥 延期提醒 ({{ overdueReqs.length }})</div>
      <table class="table">
        <thead>
          <tr><th>需求标题</th><th>负责人</th><th>截止日期</th><th>已延期</th><th>优先级</th><th>状态</th></tr>
        </thead>
        <tbody>
          <tr v-for="req in overdueReqs" :key="req.id">
            <td>
              <router-link :to="`/requirement/${req.id}`" class="link">{{ req.title }}</router-link>
            </td>
            <td class="text-muted text-medium">
              {{ req.assignee_id ? req.assignee_id.slice(0, 8) : '未指派' }}
            </td>
            <td class="text-medium">{{ formatDate(req.due_date) }}</td>
            <td>
              <span class="overdue-tag">{{ daysOverdue(req.due_date) }} 天</span>
            </td>
            <td><span :class="['priority-badge', req.priority]">{{ req.priority }}</span></td>
            <td><span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Unassigned requirements -->
    <div v-if="unassignedReqs.length" class="card mb-16">
      <div class="card-title" style="color:#d97706;">⚠ 待指派需求 ({{ unassignedReqs.length }})</div>
      <table class="table">
        <thead>
          <tr><th>需求标题</th><th>优先级</th><th>迭代</th><th>状态</th></tr>
        </thead>
        <tbody>
          <tr v-for="req in unassignedReqs" :key="req.id">
            <td>
              <router-link :to="`/requirement/${req.id}`" class="link">{{ req.title }}</router-link>
            </td>
            <td><span :class="['priority-badge', req.priority]">{{ req.priority }}</span></td>
            <td class="text-muted text-medium">{{ getIterationName(req.iteration_id) }}</td>
            <td><span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Per-developer cards -->
    <div v-if="!loading">
      <div v-if="developerGroups.length === 0" class="card">
        <div class="empty-state">
          <div class="empty-state-icon">◈</div>
          <div class="empty-state-text">暂无已指派的需求</div>
        </div>
      </div>
      <div v-for="dev in developerGroups" :key="dev.assigneeId" class="dev-card card mb-16">
        <div class="dev-card-header">
          <div class="dev-avatar">{{ dev.assigneeId.slice(0, 2).toUpperCase() }}</div>
          <div class="dev-info">
            <div class="dev-name">开发者 {{ dev.assigneeId.slice(0, 8) }}</div>
            <div class="dev-stats text-muted text-small">
              进行中 {{ dev.inProgress }} 个 · 已完成 {{ dev.completed }} 个
            </div>
          </div>
          <div class="dev-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: dev.progressPct + '%' }"></div>
            </div>
            <span class="progress-pct">{{ dev.progressPct }}%</span>
          </div>
        </div>

        <div class="req-list">
          <div v-for="req in dev.requirements" :key="req.id" class="req-row">
            <div class="req-row-left">
              <span :class="['req-status-dot', req.status]"></span>
              <router-link :to="`/requirement/${req.id}`" class="req-title link">
                {{ req.title }}
              </router-link>
            </div>
            <div class="req-row-right">
              <span :class="['priority-badge', req.priority]">{{ req.priority }}</span>
              <span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span>
              <span class="text-muted text-small">{{ getIterationName(req.iteration_id) }}</span>
            </div>
          </div>
        </div>
      </div>
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
  inProgress: filteredReqs.value.filter(r => ['in_progress', 'pending_review', 'claimed'].includes(r.status)).length,
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

const formatDate = (d: string) => {
  if (!d) return '-'
  return new Date(d).toISOString().slice(0, 10)
}

const developerGroups = computed(() => {
  const assigned = filteredReqs.value.filter(r => r.assignee_id)
  const groups: Record<string, any[]> = {}
  for (const req of assigned) {
    if (!groups[req.assignee_id]) groups[req.assignee_id] = []
    groups[req.assignee_id].push(req)
  }
  return Object.entries(groups).map(([assigneeId, reqs]) => {
    const completed = reqs.filter(r => r.status === 'completed').length
    const inProgress = reqs.filter(r => ['in_progress', 'pending_review', 'claimed'].includes(r.status)).length
    return {
      assigneeId,
      requirements: reqs,
      completed,
      inProgress,
      progressPct: reqs.length ? Math.round((completed / reqs.length) * 100) : 0,
    }
  })
})

const statusText = (s: string) => ({
  draft: '草稿', pending_analysis: '待分析', analyzed: '已分析',
  assigned: '已指派', claimed: '已领取', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const getIterationName = (id: string) => iterations.value.find((i: any) => i.id === id)?.name || '-'

const fetchData = async () => {
  loading.value = true
  try {
    const [reqRes, iterRes] = await Promise.all([requirementsApi.list(), iterationsApi.list()])
    requirements.value = reqRes.data
    iterations.value = iterRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.dev-card { padding: 0; overflow: hidden; }

.dev-card-header {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; border-bottom: 1px solid #f0f1f5;
  background: #fafafa;
}

.dev-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

.dev-info { flex: 1; min-width: 0; }
.dev-name { font-size: 14px; font-weight: 600; color: #111827; }
.dev-stats { margin-top: 2px; }

.dev-progress { display: flex; align-items: center; gap: 10px; }
.progress-bar {
  width: 120px; height: 6px; background: #f0f1f5;
  border-radius: 3px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 3px; transition: width 0.3s;
}
.progress-pct { font-size: 13px; font-weight: 600; color: #6366f1; min-width: 36px; }

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
.req-status-dot.claimed { background: #6366f1; }

.req-title { font-size: 13.5px; font-weight: 500; }

.overdue-tag {
  display: inline-block;
  background: #fee2e2; color: #b91c1c;
  font-size: 12px; font-weight: 600;
  padding: 2px 8px; border-radius: 10px;
}
</style>
