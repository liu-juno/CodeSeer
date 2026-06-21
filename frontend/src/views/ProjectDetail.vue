<template>
  <div class="project-detail">
    <el-link underline="never" type="primary" @click="$router.push('/projects')" style="margin-bottom:16px; display:inline-block;">
      ← 返回项目列表
    </el-link>

    <div v-if="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else-if="project">
      <el-card shadow="never" style="margin-bottom:16px;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
          <div>
            <h1 class="detail-title">{{ project.name }}</h1>
            <el-text v-if="project.description" class="text-muted" style="margin-top:6px; display:block;">
              {{ project.description }}
            </el-text>
            <el-text class="text-small text-muted" style="margin-top:10px; display:block;">
              创建于 {{ formatDate(project.created_at) }} · ID: {{ project.id.slice(0, 8) }}...
            </el-text>
          </div>
          <el-tag :type="statusType(project.status)" size="large">{{ statusText(project.status) }}</el-tag>
        </div>
      </el-card>

      <el-row :gutter="14" style="margin-bottom:16px;">
        <el-col :span="6">
          <el-card shadow="never" body-style="padding:16px;">
            <div style="display:flex; align-items:center; gap:14px;">
              <div class="stat-icon blue">↻</div>
              <div>
                <div class="stat-value">{{ stats.iteration_count || 0 }}</div>
                <div class="stat-label">迭代数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" body-style="padding:16px;">
            <div style="display:flex; align-items:center; gap:14px;">
              <div class="stat-icon amber">◇</div>
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
              <div class="stat-icon purple">%</div>
              <div>
                <div class="stat-value">{{ stats.progress_pct || 0 }}%</div>
                <div class="stat-label">完成率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

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

const statusType = (s: string) => ({ active: 'primary', archived: 'info', completed: 'success' }[s] || 'info')
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
.detail-title { font-size: 22px; font-weight: 700; color: #1f2329; letter-spacing: -0.3px; margin: 0; }
.stat-value { font-size: 22px; font-weight: 700; color: #1f2329; line-height: 1; }
.stat-label { font-size: 12px; color: #969ba4; margin-top: 3px; }
.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.stat-icon.blue { background: rgba(45, 91, 255, 0.1); }
.stat-icon.amber { background: rgba(255, 154, 46, 0.1); }
.stat-icon.green { background: rgba(0, 168, 112, 0.1); }
.stat-icon.purple { background: rgba(139, 92, 246, 0.1); }
</style>
