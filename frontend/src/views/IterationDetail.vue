<template>
  <div class="iteration-detail">
    <el-link underline="never" type="primary" @click="$router.back()" style="margin-bottom:16px; display:inline-block;">
      ← 返回
    </el-link>

    <div v-if="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else-if="iteration">
      <el-card shadow="never" style="margin-bottom:16px;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
          <div>
            <h1 class="detail-title">{{ iteration.name }}</h1>
            <el-text v-if="iteration.description" class="text-muted" style="margin-top:6px; display:block;">
              {{ iteration.description }}
            </el-text>
            <el-text class="text-small text-muted" style="margin-top:10px; display:block;">
              所属项目：{{ getProjectName(iteration.project_id) }} ·
              计划发布：{{ iteration.planned_release_date ? formatDate(iteration.planned_release_date) : '未设置' }} ·
              实际发布：{{ iteration.actual_release_date ? formatDate(iteration.actual_release_date) : '未发布' }}
            </el-text>
          </div>
          <div style="display:flex; flex-direction:column; gap:8px; align-items:flex-end;">
            <el-tag :type="statusType(iteration.status)" size="large">{{ statusText(iteration.status) }}</el-tag>
            <el-button
              v-if="iteration.status !== 'released' && iteration.status !== 'archived'"
              type="primary"
              @click="releaseIteration"
              :loading="releasing"
            >
              发布迭代
            </el-button>
          </div>
        </div>
      </el-card>

      <el-row :gutter="14" style="margin-bottom:16px;">
        <el-col :span="6">
          <el-card shadow="never" body-style="padding:16px;">
            <div style="display:flex; align-items:center; gap:14px;">
              <div class="stat-icon blue">◇</div>
              <div>
                <div class="stat-value">{{ stats.total_requirements || 0 }}</div>
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
                <div class="stat-value">{{ stats.completed || 0 }}</div>
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
                <div class="stat-value">{{ stats.in_progress || 0 }}</div>
                <div class="stat-label">进行中</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" body-style="padding:16px;">
            <div style="display:flex; align-items:center; gap:14px;">
              <div class="stat-icon purple">%</div>
              <div>
                <div class="stat-value">{{ stats.progress_pct || 0 }}%</div>
                <div class="stat-label">完成率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" style="margin-bottom:16px;">
        <template #header>
          <div class="card-header">状态分布</div>
        </template>
        <div class="dist-bar">
          <div
            v-for="(count, status) in stats.status_distribution || {}"
            :key="status"
            :class="['dist-segment', status]"
            :style="{ width: ((count / (stats.total_requirements || 1)) * 100) + '%' }"
            :title="`${statusText(status)}: ${count}`"
          ></div>
        </div>
        <div class="dist-legend">
          <div v-for="(count, status) in stats.status_distribution || {}" :key="status" class="legend-item">
            <span :class="['dist-segment-inline', status]"></span>
            <span>{{ statusText(status) }} · {{ count }}</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" body-style="padding:0;">
        <template #header>
          <div style="font-weight:600;">迭代需求 ({{ requirements.length }})</div>
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
              <el-tag :type="reqStatusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="assignee_id" label="指派给" width="120">
            <template #default="{ row }">
              <el-text class="text-muted text-small">{{ row.assignee_id ? row.assignee_id.slice(0, 8) : '未指派' }}</el-text>
            </template>
          </el-table-column>
          <el-table-column prop="due_date" label="截止日期" width="120">
            <template #default="{ row }">
              <el-text class="text-muted text-small">{{ row.due_date ? formatDate(row.due_date) : '-' }}</el-text>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { iterationsApi, projectsApi, requirementsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const iteration = ref<any>(null)
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const stats = ref<any>({})
const loading = ref(false)
const releasing = ref(false)

const statusType = (s: string) => ({
  planning: 'info', development: 'primary', testing: 'warning',
  released: 'success', archived: 'info',
}[s] || 'info')
const reqStatusType = (s: string) => ({
  draft: 'info', assigned: 'primary', in_progress: 'primary',
  pending_review: 'warning', review_approved: 'success', review_rejected: 'danger', completed: 'success',
}[s] || 'info')
const priorityType = (p: string) => ({ P0: 'danger', P1: 'warning', P2: 'info', P3: 'info' }[p] || 'info')

const statusText = (s: string) => ({
  planning: '规划中', development: '开发中', testing: '测试中',
  released: '已发布', archived: '已归档',
  draft: '草稿', assigned: '已指派', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const getProjectName = (id: string) => projects.value.find((p: any) => p.id === id)?.name || '-'

const releaseIteration = async () => {
  try {
    await ElMessageBox.confirm('发布迭代将归档所有该迭代下需求的草稿文档，无法撤销。确认发布？', '提示', { type: 'warning' })
    releasing.value = true
    const res = await iterationsApi.release(route.params.id as string)
    if (res.data.success) {
      ElMessage.success(`发布成功。归档了 ${res.data.archived_documents} 份文档。`)
      fetchData()
    }
  } catch (e) { if (e !== 'cancel') console.error(e) }
  finally { releasing.value = false }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [itRes, pRes, rRes, sRes] = await Promise.all([
      iterationsApi.get(route.params.id as string),
      projectsApi.list(),
      requirementsApi.byIteration(route.params.id as string),
      iterationsApi.statistics(route.params.id as string),
    ])
    iteration.value = itRes.data
    projects.value = pRes.data.items ?? pRes.data
    requirements.value = rRes.data
    stats.value = sRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.detail-title { font-size: 22px; font-weight: 700; color: #1f2329; letter-spacing: -0.3px; margin: 0 0 8px 0; }
.stat-value { font-size: 22px; font-weight: 700; color: #1f2329; line-height: 1; }
.stat-label { font-size: 12px; color: #969ba4; margin-top: 3px; }
.stat-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.stat-icon.blue { background: rgba(45, 91, 255, 0.1); }
.stat-icon.green { background: rgba(0, 168, 112, 0.1); }
.stat-icon.amber { background: rgba(255, 154, 46, 0.1); }
.stat-icon.purple { background: rgba(139, 92, 246, 0.1); }
.dist-bar {
  display: flex; height: 8px; border-radius: 4px; overflow: hidden;
  background: #f0f1f5; margin-bottom: 14px;
}
.dist-segment { height: 100%; transition: width 0.3s; }
.dist-segment.completed  { background: #10b981; }
.dist-segment.in_progress{ background: #f59e0b; }
.dist-segment.pending_review { background: #ec4899; }
.dist-segment.assigned { background: #6366f1; }
.dist-segment.review_approved { background: #06b6d4; }
.dist-segment.draft    { background: #9ca3af; }
.dist-legend { display: flex; flex-wrap: wrap; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #6b7280; }
.dist-segment-inline { width: 10px; height: 10px; border-radius: 2px; }
.dist-segment-inline.completed  { background: #10b981; }
.dist-segment-inline.in_progress{ background: #f59e0b; }
.dist-segment-inline.pending_review { background: #ec4899; }
.dist-segment-inline.assigned { background: #6366f1; }
.dist-segment-inline.review_approved { background: #06b6d4; }
.dist-segment-inline.draft    { background: #9ca3af; }
</style>
