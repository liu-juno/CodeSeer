<template>
  <div class="iteration-detail">
    <div class="back-row">
      <router-link to="/iterations" class="back-link">← 返回迭代列表</router-link>
    </div>

    <div v-if="loading" class="card"><div class="text-muted">加载中...</div></div>

    <template v-else-if="iteration">
      <!-- Header -->
      <div class="card header-card">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
          <div>
            <h1 class="detail-title">{{ iteration.name }}</h1>
            <p v-if="iteration.description" class="text-muted text-medium" style="margin-top:6px">
              {{ iteration.description }}
            </p>
            <div class="text-small text-muted" style="margin-top:10px;">
              所属项目：{{ getProjectName(iteration.project_id) }} ·
              计划发布：{{ iteration.planned_release_date ? formatDate(iteration.planned_release_date) : '未设置' }} ·
              实际发布：{{ iteration.actual_release_date ? formatDate(iteration.actual_release_date) : '未发布' }}
            </div>
          </div>
          <div style="display:flex; flex-direction:column; gap:8px; align-items:flex-end;">
            <span :class="['status-badge', iteration.status]" style="font-size:13px; padding:5px 14px;">
              {{ statusText(iteration.status) }}
            </span>
            <button
              v-if="iteration.status !== 'released' && iteration.status !== 'archived'"
              class="btn btn-primary"
              @click="releaseIteration"
              :disabled="releasing"
            >
              {{ releasing ? '发布中...' : '🚀 发布迭代' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon indigo">◇</div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.total_requirements || 0 }}</div>
            <div class="stat-label">总需求</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">✓</div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.completed || 0 }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon amber">↻</div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.in_progress || 0 }}</div>
            <div class="stat-label">进行中</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon purple">%</div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.progress_pct || 0 }}%</div>
            <div class="stat-label">完成率</div>
          </div>
        </div>
      </div>

      <!-- Status distribution -->
      <div class="card">
        <div class="card-title">状态分布</div>
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
      </div>

      <!-- Requirements in this iteration -->
      <div class="card" style="padding:0; overflow:hidden;">
        <div style="padding:16px 20px; border-bottom:1px solid #f0f1f5;">
          <div class="card-title" style="margin:0">迭代需求 ({{ requirements.length }})</div>
        </div>
        <table class="table">
          <thead>
            <tr>
              <th>需求</th><th>优先级</th><th>状态</th><th>指派给</th><th>截止日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in requirements" :key="req.id">
              <td>
                <router-link :to="`/requirements/${req.id}`" class="link">{{ req.title }}</router-link>
              </td>
              <td><span :class="['priority-badge', req.priority]">{{ req.priority }}</span></td>
              <td><span :class="['status-badge', req.status]">{{ statusText(req.status) }}</span></td>
              <td class="text-muted text-small">{{ req.assignee_id ? req.assignee_id.slice(0, 8) : '未指派' }}</td>
              <td class="text-muted text-small">{{ req.due_date ? formatDate(req.due_date) : '-' }}</td>
            </tr>
            <tr v-if="requirements.length === 0">
              <td colspan="5">
                <div class="empty-state">
                  <div class="empty-state-icon">◇</div>
                  <div class="empty-state-text">该迭代下暂无需求</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { iterationsApi, projectsApi, requirementsApi } from '@/api'

const route = useRoute()
const iteration = ref<any>(null)
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const stats = ref<any>({})
const loading = ref(false)
const releasing = ref(false)

const statusText = (s: string) => ({
  planning: '规划中', development: '开发中', testing: '测试中',
  released: '已发布', archived: '已归档',
  draft: '草稿', pending_analysis: '待分析', analyzed: '已分析',
  assigned: '已指派', claimed: '已领取', in_progress: '开发中',
  pending_review: '待评审', review_approved: '评审通过',
  review_rejected: '评审驳回', completed: '已完成',
}[s] || s)

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const getProjectName = (id: string) => projects.value.find((p: any) => p.id === id)?.name || '-'

const releaseIteration = async () => {
  if (!confirm('发布迭代将归档所有该迭代下需求的草稿文档，无法撤销。确认发布？')) return
  releasing.value = true
  try {
    const res = await fetch(`/api/iterations/${route.params.id}/release`, { method: 'POST' })
    const res = await iterationsApi.release(route.params.id as string)
    if (res.data.success) {
      alert(`发布成功。归档了 ${res.data.archived_documents} 份文档。`)
      fetchData()
    }
  } catch (e) { console.error(e) }
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
    projects.value = pRes.data
    requirements.value = rRes.data
    stats.value = sRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.back-row { margin-bottom: 16px; }
.back-link { color: #6b7280; text-decoration: none; font-size: 13.5px; font-weight: 500; }
.back-link:hover { color: #6366f1; }

.header-card { padding: 24px; }
.detail-title { font-size: 22px; font-weight: 700; color: #111827; letter-spacing: -0.3px; }

.dist-bar {
  display: flex; height: 8px; border-radius: 4px; overflow: hidden;
  background: #f0f1f5; margin-bottom: 14px;
}
.dist-segment { height: 100%; transition: width 0.3s; }
.dist-segment.completed  { background: #10b981; }
.dist-segment.in_progress{ background: #f59e0b; }
.dist-segment.pending_review { background: #ec4899; }
.dist-segment.assigned { background: #6366f1; }
.dist-segment.claimed  { background: #8b5cf6; }
.dist-segment.review_approved { background: #06b6d4; }
.dist-segment.draft    { background: #9ca3af; }

.dist-legend { display: flex; flex-wrap: wrap; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #6b7280; }
.dist-segment-inline {
  width: 10px; height: 10px; border-radius: 2px;
}
.dist-segment-inline.completed  { background: #10b981; }
.dist-segment-inline.in_progress{ background: #f59e0b; }
.dist-segment-inline.pending_review { background: #ec4899; }
.dist-segment-inline.assigned { background: #6366f1; }
.dist-segment-inline.claimed  { background: #8b5cf6; }
.dist-segment-inline.review_approved { background: #06b6d4; }
.dist-segment-inline.draft    { background: #9ca3af; }
</style>
