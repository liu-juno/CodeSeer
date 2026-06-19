<template>
  <div class="project-detail">
    <div class="back-row">
      <router-link to="/projects" class="back-link">← 返回项目列表</router-link>
    </div>

    <div v-if="loading" class="card"><div class="text-muted">加载中...</div></div>

    <template v-else-if="project">
      <!-- Header -->
      <div class="card header-card">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
          <div>
            <h1 class="detail-title">{{ project.name }}</h1>
            <p v-if="project.description" class="text-muted text-medium" style="margin-top:6px">
              {{ project.description }}
            </p>
            <div class="text-small text-muted" style="margin-top:10px;">
              创建于 {{ formatDate(project.created_at) }} ·
              ID: <code class="text-small">{{ project.id.slice(0, 8) }}...</code>
            </div>
          </div>
          <span :class="['status-badge', project.status]" style="font-size:13px; padding:5px 14px;">
            {{ statusText(project.status) }}
          </span>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon blue">↻</div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.iteration_count || 0 }}</div>
            <div class="stat-label">迭代数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon amber">◇</div>
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
          <div class="stat-icon purple">%</div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.progress_pct || 0 }}%</div>
            <div class="stat-label">完成率</div>
          </div>
        </div>
      </div>

      <router-view />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi } from '@/api'

const route = useRoute()
const project = ref<any>(null)
const stats = ref<any>({})
const loading = ref(false)

const statusText = (s: string) => ({
  active: '进行中', archived: '已归档', completed: '已完成',
  planning: '规划中', development: '开发中', testing: '测试中',
  released: '已发布',
}[s] || s)

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const [pRes, sRes] = await Promise.all([
      projectsApi.get(route.params.id as string),
      projectsApi.statistics(route.params.id as string),
    ])
    project.value = pRes.data
    stats.value = sRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.back-row { margin-bottom: 16px; }
.back-link { color: var(--color-text-secondary); text-decoration: none; font-size: 13.5px; font-weight: 500; }
.back-link:hover { color: var(--color-primary); }

.header-card { padding: 24px; }
.detail-title { font-size: 22px; font-weight: 700; color: var(--color-text-primary); letter-spacing: -0.3px; }

</style>
