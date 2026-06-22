<template>
  <div class="dashboard">
    <div class="page-header">
      <div style="display:flex; align-items:center; gap:10px;">
        <el-select v-model="selectedIteration" placeholder="选择迭代" style="width:200px;" clearable>
          <el-option v-for="iteration in iterations" :key="iteration.id" :label="iteration.name" :value="iteration.id" />
        </el-select>
      </div>
    </div>

    <el-row :gutter="14" style="margin-bottom:16px;">
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon indigo">◇</div>
            <div>
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总需求</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon green">✓</div>
            <div>
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon amber">↻</div>
            <div>
              <div class="stat-value">{{ stats.inProgress }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" body-style="padding:16px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="stat-icon purple">◈</div>
            <div>
              <div class="stat-value">{{ stats.pending }}</div>
              <div class="stat-label">待领取</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-title">我的任务</div>
          </template>
          <div v-if="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <el-empty v-else-if="requirements.length === 0" description="暂无任务" />
          <div v-else class="requirement-list">
            <div v-for="req in requirements.slice(0, 6)" :key="req.id" class="requirement-item">
              <div class="requirement-header">
                <el-link type="primary" underline="never" @click="$router.push(`/requirement/${req.id}`)">
                  {{ req.title }}
                </el-link>
                <el-tag :type="statusType(req.status)" size="small">{{ statusText(req.status) }}</el-tag>
              </div>
              <div class="requirement-meta text-small text-muted">
                {{ getIterationName(req.iteration_id) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <span style="font-weight:600; margin:0;">待办需求</span>
              <el-link type="primary" underline="never" @click="$router.push('/requirements')">查看全部</el-link>
            </div>
          </template>
          <div v-if="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <el-empty v-else-if="pendingRequirements.length === 0" description="暂无待办" />
          <el-table v-else :data="pendingRequirements" stripe size="small">
            <el-table-column prop="title" label="标题" min-width="180">
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
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
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
  pending: requirements.value.filter(r => ['draft', 'assigned'].includes(r.status)).length,
}))

const pendingRequirements = computed(() =>
  requirements.value.filter(r => r.status !== 'completed').slice(0, 5)
)

const statusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success', review_rejected: 'danger', completed: 'success',
}[s] || 'info')
const priorityType = (p: string) => ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')

const statusText = (status: string) => ({
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[status] || status)

const getIterationName = (iterationId: string) => {
  const it = iterations.value.find((i: any) => i.id === iterationId)
  return it?.name || '-'
}

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
.stat-icon.green { background: rgba(0, 168, 112, 0.1); }
.stat-icon.amber { background: rgba(255, 154, 46, 0.1); }
.stat-icon.purple { background: rgba(139, 92, 246, 0.1); }
.requirement-list { display: flex; flex-direction: column; gap: 10px; }
.requirement-item {
  padding: 11px 13px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #f0f1f5;
  transition: border-color 0.15s;
}
.requirement-item:hover { border-color: #c7d2fe; }
.requirement-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.requirement-meta { margin-top: 4px; }
</style>
