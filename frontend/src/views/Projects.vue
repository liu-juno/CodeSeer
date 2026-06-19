<template>
  <div class="projects-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目管理</h1>
        <p class="page-subtitle">管理所有产品项目</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <span>＋</span> 创建项目
      </button>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state">
        <div class="empty-state-text text-muted">加载中...</div>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>项目名称</th>
            <th>描述</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="proj in projects" :key="proj.id">
            <td style="font-weight:500">
              <router-link :to="`/project/${proj.id}`" class="link">{{ proj.name }}</router-link>
            </td>
            <td class="text-muted text-medium">{{ proj.description || '-' }}</td>
            <td>
              <span :class="['status-badge', proj.status]">{{ statusText(proj.status) }}</span>
            </td>
            <td class="text-muted text-small">{{ formatDate(proj.created_at) }}</td>
          </tr>
          <tr v-if="projects.length === 0">
            <td colspan="4">
              <div class="empty-state">
                <div class="empty-state-icon">▦</div>
                <div class="empty-state-text">暂无项目，点击「创建项目」开始</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>创建项目</h3>
          <button class="modal-close" @click="showCreateModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">项目名称 <span class="required">*</span></label>
            <input v-model="newProject.name" type="text" class="form-input" placeholder="如：CodeSeer Web" />
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">项目描述</label>
            <textarea v-model="newProject.description" class="form-input" placeholder="简要描述项目目标..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn btn-primary" :disabled="!newProject.name.trim()" @click="createProject">创建项目</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { projectsApi } from '@/api'

const projects = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)

const newProject = ref({ name: '', description: '' })

const statusText = (status: string) => {
  const map: Record<string, string> = { active: '进行中', archived: '已归档', completed: '已完成' }
  return map[status] || status
}

const formatDate = (date: string) => new Date(date).toLocaleDateString('zh-CN')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await projectsApi.list()
    projects.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  try {
    await projectsApi.create(newProject.value)
    showCreateModal.value = false
    newProject.value = { name: '', description: '' }
    fetchData()
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchData)
</script>
