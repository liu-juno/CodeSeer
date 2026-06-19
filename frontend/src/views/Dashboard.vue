<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">当前迭代进度一览</p>
      </div>
      <div style="display:flex; align-items:center; gap:10px;">
        <select v-model="selectedIteration" class="form-input" style="width:200px;">
          <option value="">选择迭代</option>
          <option v-for="iteration in iterations" :key="iteration.id" :value="iteration.id">
            {{ iteration.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Stats row -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon indigo">◇</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总需求</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">✓</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon amber">↻</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.inProgress }}</div>
          <div class="stat-label">进行中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">◈</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待领取</div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- My tasks -->
      <div class="card">
        <div class="card-title">我的任务</div>
        <div v-if="loading" class="text-muted text-medium">加载中...</div>
        <div v-else-if="requirements.length === 0" class="empty-state" style="padding:24px 0">
          <div class="empty-state-icon">◇</div>
          <div class="empty-state-text">暂无任务</div>
        </div>
        <div v-else class="requirement-list">
          <div v-for="req in requirements.slice(0, 6)" :key="req.id" class="requirement-item">
            <div class="requirement-header">
              <router-link :to="`/requirement/${req.id}`" class="requirement-title link">
                {{ req.title }}
              </router-link>
              <span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span>
            </div>
            <div class="requirement-meta text-small text-muted">
              {{ getIterationName(req.iteration_id) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Pending requirements -->
      <div class="card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
          <span class="card-title" style="margin-bottom:0">待办需求</span>
          <router-link to="/requirements" class="link text-small">查看全部</router-link>
        </div>
        <div v-if="loading" class="text-muted text-medium">加载中...</div>
        <div v-else-if="pendingRequirements.length === 0" class="empty-state" style="padding:24px 0">
          <div class="empty-state-icon">✓</div>
          <div class="empty-state-text">暂无待办</div>
        </div>
        <table v-else class="table" style="margin:-4px -4px">
          <thead>
            <tr>
              <th>标题</th>
              <th>优先级</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in pendingRequirements" :key="req.id">
              <td>
                <router-link :to="`/requirement/${req.id}`" class="link">{{ req.title }}</router-link>
              </td>
              <td>
                <span :class="['priority-badge', req.priority]">{{ req.priority }}</span>
              </td>
              <td>
                <span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { requirementsApi, iterationsApi } from '@/api'

const requirements = ref<any[]>([])
const iterations = ref<any[]>([])
const selectedIteration = ref('')
const loading = ref(false)

const stats = computed(() => ({
  total: requirements.value.length,
  completed: requirements.value.filter(r => r.status === 'completed').length,
  inProgress: requirements.value.filter(r => ['in_progress', 'pending_review'].includes(r.status)).length,
  pending: requirements.value.filter(r => ['draft', 'assigned', 'claimed'].includes(r.status)).length,
}))

const pendingRequirements = computed(() =>
  requirements.value.filter(r => r.status !== 'completed').slice(0, 5)
)

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

const fetchData = async () => {
  loading.value = true
  try {
    const [reqRes, iterRes] = await Promise.all([requirementsApi.list(), iterationsApi.list()])
    requirements.value = reqRes.data
    iterations.value = iterRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.requirement-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.requirement-item {
  padding: 11px 13px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #f0f1f5;
  transition: border-color 0.15s;
}

.requirement-item:hover {
  border-color: #c7d2fe;
}

.requirement-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.requirement-title {
  font-weight: 500;
  font-size: 13.5px;
}

.requirement-meta {
  margin-top: 4px;
}
</style>
