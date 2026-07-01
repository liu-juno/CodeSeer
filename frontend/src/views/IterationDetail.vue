<template>
  <div class="iteration-detail" v-if="iteration">
    <!-- ── Info header ─────────────────────────────────────── -->
    <div class="detail-header">
      <div class="header-main">
        <div class="header-title-row">
          <h1 class="detail-title">{{ iteration.name }}</h1>
          <el-dropdown trigger="click" @command="changeStatus">
            <el-tag :type="statusType(iteration.status)" size="large" style="cursor:pointer;">
              {{ statusText(iteration.status) }} ▾
            </el-tag>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="s in STATUS_FLOW[iteration.status] || []"
                  :key="s"
                  :command="s"
                >
                  <el-tag :type="statusType(s)" size="small" style="margin-right:6px;">{{ statusText(s) }}</el-tag>
                  {{ STATUS_ACTION[s] }}
                </el-dropdown-item>
                <el-dropdown-item v-if="!(STATUS_FLOW[iteration.status]?.length)" disabled>
                  已是终态
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="header-meta">
          <span>{{ formatDate(iteration.planned_release_date) }}</span>
          <span class="meta-sep">→</span>
          <span>{{ iteration.actual_release_date ? formatDate(iteration.actual_release_date) : '进行中' }}</span>
        </div>
      </div>

      <div class="header-progress">
        <div class="progress-label">
          <span class="progress-pct">{{ stats.progress_pct || 0 }}%</span>
          <span class="progress-sub">{{ stats.completed || 0 }} / {{ stats.total_requirements || 0 }} 完成</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (stats.progress_pct || 0) + '%' }"
          />
        </div>
      </div>

    </div>

    <!-- ── Sub-tabs ───────────────────────────────────────── -->
    <div class="detail-tabs">
      <span
        v-for="tab in TABS"
        :key="tab.key"
        :class="['detail-tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </span>
    </div>

    <div v-if="loading" class="tab-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <template v-else>
      <!-- 概览 -->
      <div v-show="activeTab === 'overview'">
        <el-row :gutter="14" style="margin-bottom: 1rem;">
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon blue">◇</div>
                <div><div class="stat-value">{{ stats.total_requirements || 0 }}</div><div class="stat-label">总需求</div></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon green">✓</div>
                <div><div class="stat-value">{{ stats.completed || 0 }}</div><div class="stat-label">已完成</div></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon amber">↻</div>
                <div><div class="stat-value">{{ stats.in_progress || 0 }}</div><div class="stat-label">进行中</div></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" body-style="padding:16px;">
              <div class="stat-cell">
                <div class="stat-icon purple">%</div>
                <div><div class="stat-value">{{ stats.progress_pct || 0 }}%</div><div class="stat-label">完成率</div></div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="never">
          <template #header><span class="card-title">状态分布</span></template>
          <div class="dist-bar">
            <div
              v-for="(count, status) in stats.status_distribution || {}"
              :key="status"
              :class="['dist-segment', status]"
              :style="{ width: ((count / (stats.total_requirements || 1)) * 100) + '%' }"
              :title="`${reqStatusText(status as string)}: ${count}`"
            />
          </div>
          <div class="dist-legend">
            <div v-for="(count, status) in stats.status_distribution || {}" :key="status" class="legend-item">
              <span :class="['dist-dot', status]" />
              <span>{{ reqStatusText(status as string) }} · {{ count }}</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 需求 -->
      <div v-show="activeTab === 'requirements'">
        <el-card shadow="never" body-style="padding:0;">
          <template #header>
            <span class="card-title">迭代需求 ({{ requirements.length }})</span>
          </template>
          <el-table :data="requirements" stripe style="width:100%">
            <el-table-column prop="title" label="需求" min-width="240">
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
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="reqStatusType(row.status)" size="small">{{ reqStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="assignee_id" label="指派给" width="120">
              <template #default="{ row }">
                <span class="text-muted text-small">{{ row.assignee_id ? row.assignee_id.slice(0, 8) : '未指派' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止日期" width="120">
              <template #default="{ row }">
                <span class="text-muted text-small">{{ row.due_date ? formatDate(row.due_date) : '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <!-- 缺陷 -->
      <div v-show="activeTab === 'defects'">
        <el-empty description="缺陷视图待开发" />
      </div>

      <!-- 成员 -->
      <div v-show="activeTab === 'members'">
        <el-empty description="成员视图待开发" />
      </div>
    </template>
  </div>

  <div v-else-if="loading">
    <el-skeleton :rows="6" animated />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { iterationsApi, requirementsApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const iteration = ref<any>(null)
const requirements = ref<any[]>([])
const stats = ref<any>({})
const loading = ref(false)
const activeTab = ref<'overview' | 'requirements' | 'defects' | 'members'>('overview')

const TABS = [
  { key: 'overview',      label: '概览' },
  { key: 'requirements',  label: '需求' },
  { key: 'defects',       label: '缺陷' },
  { key: 'members',       label: '成员' },
] as const

const STATUS_FLOW: Record<string, string[]> = {
  planning:    ['development'],
  development: ['testing'],
  testing:     ['released'],
  released:    ['archived'],
  archived:    [],
}

const STATUS_ACTION: Record<string, string> = {
  development: '开始开发',
  testing:     '进入测试',
  released:    '发布',
  archived:    '关闭',
}

const statusType = (s: string) => ({
  planning: 'info', development: 'primary', testing: 'warning',
  released: 'success', archived: 'info',
}[s] || 'info')

const statusText = (s: string) => ({
  planning: '规划中', development: '开发中', testing: '测试中',
  released: '已发布', archived: '已关闭',
}[s] || s)

const changeStatus = async (newStatus: string) => {
  if (!iteration.value) return
  try {
    await iterationsApi.update(iteration.value.id, { status: newStatus })
    iteration.value.status = newStatus
    ElMessage.success(`状态已更新为「${statusText(newStatus)}」`)
  } catch (e) {
    ElMessage.error('状态更新失败')
  }
}

const reqStatusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success',
  review_rejected: 'danger', completed: 'success',
}[s] || 'info')

const reqStatusText = (s: string) => ({
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const priorityType = (p: string) =>
  ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')

const formatDate = (d: string) =>
  d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const [itRes, rRes, sRes] = await Promise.all([
      iterationsApi.get(route.params.id as string),
      requirementsApi.byIteration(route.params.id as string),
      iterationsApi.statistics(route.params.id as string),
    ])
    iteration.value = itRes.data
    requirements.value = rRes.data
    stats.value = sRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.iteration-detail { display: flex; flex-direction: column; gap: 1rem; }

/* Info header */
.detail-header {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-card);
  padding: clamp(12px, 1.5vw, 20px);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.header-main { flex: 1; min-width: 0; }

.header-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.375rem;
  flex-wrap: wrap;
}

.detail-title {
  font-size: clamp(1rem, 1.5vw, 1.375rem);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.meta-sep { color: var(--text-muted); }

/* Progress */
.header-progress { width: clamp(140px, 20vw, 220px); }

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.375rem;
}

.progress-pct { font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.progress-sub { font-size: 0.75rem; color: var(--text-muted); }

.progress-bar {
  height: 6px;
  background: var(--border-default);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.4s ease;
}

/* Tabs */
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-default);
}

.detail-tab {
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
  user-select: none;
}

.detail-tab:hover { color: var(--text-primary); }
.detail-tab.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 500; }

.tab-loading { margin-top: 1rem; }

/* Stat cards */
.stat-cell { display: flex; align-items: center; gap: 0.875rem; }
.stat-value { font-size: 1.375rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 3px; }
.stat-icon {
  width: 2.5rem; height: 2.5rem; border-radius: 0.625rem;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.125rem; flex-shrink: 0;
}
.stat-icon.blue   { background: rgba(45,91,255,0.1); }
.stat-icon.green  { background: rgba(0,168,112,0.1); }
.stat-icon.amber  { background: rgba(255,154,46,0.1); }
.stat-icon.purple { background: rgba(139,92,246,0.1); }

/* Distribution bar */
.dist-bar {
  display: flex; height: 8px; border-radius: 4px;
  overflow: hidden; background: var(--border-light); margin-bottom: 0.875rem;
}
.dist-segment { height: 100%; transition: width 0.3s; }
.dist-segment.completed      { background: #10b981; }
.dist-segment.in_progress    { background: #f59e0b; }
.dist-segment.pending_review { background: #ec4899; }
.dist-segment.assigned       { background: #6366f1; }
.dist-segment.review_approved{ background: #06b6d4; }
.dist-segment.draft          { background: #9ca3af; }

.dist-legend { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.legend-item { display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: var(--text-secondary); }
.dist-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.dist-dot.completed      { background: #10b981; }
.dist-dot.in_progress    { background: #f59e0b; }
.dist-dot.pending_review { background: #ec4899; }
.dist-dot.assigned       { background: #6366f1; }
.dist-dot.review_approved{ background: #06b6d4; }
.dist-dot.draft          { background: #9ca3af; }
</style>
