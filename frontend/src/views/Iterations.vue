<template>
  <div class="iterations-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">迭代管理</h1>
        <p class="page-subtitle">管理版本迭代与发布计划</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <span>＋</span> 创建迭代
      </button>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state">
        <div class="empty-state-text text-muted">加载中...</div>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>迭代名称</th>
            <th>所属项目</th>
            <th>状态</th>
            <th>计划发布日期</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="iter in iterations" :key="iter.id">
            <td style="font-weight:500">
              <router-link :to="`/iteration/${iter.id}`" class="link">{{ iter.name }}</router-link>
            </td>
            <td class="text-muted text-medium">{{ getProjectName(iter.project_id) }}</td>
            <td>
              <span :class="['status-badge', iter.status]">{{ statusText(iter.status) }}</span>
            </td>
            <td class="text-muted text-medium">{{ iter.planned_release_date ? formatDate(iter.planned_release_date) : '-' }}</td>
            <td class="text-muted text-small">{{ formatDate(iter.created_at) }}</td>
          </tr>
          <tr v-if="iterations.length === 0">
            <td colspan="5">
              <div class="empty-state">
                <div class="empty-state-icon">↻</div>
                <div class="empty-state-text">暂无迭代，点击「创建迭代」开始</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>创建迭代</h3>
          <button class="modal-close" @click="showCreateModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">迭代名称 <span class="required">*</span></label>
            <input v-model="newIteration.name" type="text" class="form-input" placeholder="如：v1.0.0 / Sprint-1" />
          </div>
          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea v-model="newIteration.description" class="form-input" placeholder="本次迭代目标..."></textarea>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">所属项目 <span class="required">*</span></label>
              <select v-model="newIteration.project_id" class="form-input">
                <option value="">选择项目</option>
                <option v-for="proj in projects" :key="proj.id" :value="proj.id">{{ proj.name }}</option>
              </select>
            </div>
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">计划发布日期</label>
              <input v-model="newIteration.planned_release_date" type="date" class="form-input" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn btn-primary" :disabled="!newIteration.name.trim() || !newIteration.project_id" @click="createIteration">
            创建迭代
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { iterationsApi, projectsApi } from '@/api'

const route = useRoute()

const iterations = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)

const newIteration = ref({ name: '', description: '', project_id: '', planned_release_date: '' })

const statusText = (status: string) => {
  const map: Record<string, string> = {
    planning: '规划中', development: '开发中', testing: '测试中',
    released: '已发布', archived: '已归档',
  }
  return map[status] || status
}

const getProjectName = (projectId: string) => {
  const p = projects.value.find((p: any) => p.id === projectId)
  return p?.name || '-'
}

const formatDate = (date: string) => new Date(date).toLocaleDateString('zh-CN')

const fetchData = async () => {
  loading.value = true
  try {
    const [iterRes, projRes] = await Promise.all([iterationsApi.list(), projectsApi.list()])
    iterations.value = iterRes.data
    projects.value = projRes.data
    if (route.params.id) {
      iterations.value = iterations.value.filter((i: any) => i.project_id === route.params.id)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const createIteration = async () => {
  try {
    const payload = {
      ...newIteration.value,
      planned_release_date: newIteration.value.planned_release_date || null,
    }
    await iterationsApi.create(payload)
    showCreateModal.value = false
    newIteration.value = { name: '', description: '', project_id: '', planned_release_date: '' }
    fetchData()
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchData)
</script>
