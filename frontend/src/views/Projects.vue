<template>
  <div class="projects-page">
    <!-- Page Header Toolbar -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">项目管理</h1>
        <span class="text-muted text-medium" style="margin-left:12px;">{{ projects.length }} 个项目</span>
      </div>
      <div class="header-right">
        <div class="search-box">
          <span class="search-icon">⌕</span>
          <input v-model="search" type="text" class="form-input" placeholder="搜索项目..." style="width:200px; padding-left:32px;" />
        </div>
        <button class="btn btn-primary" @click="showCreateModal = true">
          <span>＋</span> 创建项目
        </button>
      </div>
    </div>

    <!-- Batch Actions Bar -->
    <div v-if="selected.length > 0" class="batch-bar">
      <span class="text-medium">已选择 <strong>{{ selected.length }}</strong> 项</span>
      <button class="btn btn-ghost btn-sm" @click="selected = []">清除</button>
      <button class="btn btn-ghost btn-sm" style="color:#ef4444;" @click="batchDelete">删除</button>
    </div>

    <!-- Table -->
    <div class="card" style="padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state">
        <div class="empty-state-text text-muted">加载中...</div>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th style="width:40px;">
              <input type="checkbox" @change="toggleSelectAll" :checked="isAllSelected" />
            </th>
            <th>项目名称</th>
            <th style="width:120px;">标识符</th>
            <th>描述</th>
            <th>状态</th>
            <th>创建时间</th>
            <th style="width:100px; text-align:right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="proj in filteredProjects" :key="proj.id" :class="{ 'row-selected': selected.includes(proj.id) }">
            <td>
              <input type="checkbox" :value="proj.id" v-model="selected" />
            </td>
            <td>
              <router-link :to="`/project/${proj.id}`" class="link" style="font-weight:600;">
                {{ proj.name }}
              </router-link>
            </td>
            <td>
              <span v-if="proj.identifier" class="identifier-badge">{{ proj.identifier }}</span>
              <span v-else class="text-muted text-small">—</span>
            </td>
            <td class="text-muted text-medium">{{ proj.description || '—' }}</td>
            <td>
              <span :class="['status-badge', proj.status]">{{ statusText(proj.status) }}</span>
            </td>
            <td class="text-muted text-small">{{ formatDate(proj.created_at) }}</td>
            <td style="text-align:right;">
              <div class="action-btns">
                <router-link :to="`/project/${proj.id}`" class="btn btn-ghost btn-sm">查看</router-link>
                <button class="btn btn-ghost btn-sm" @click="deleteProject(proj.id)" style="color:#ef4444;">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredProjects.length === 0">
            <td colspan="7">
              <div class="empty-state">
                <div class="empty-state-icon">▦</div>
                <div class="empty-state-text">暂无项目，点击「创建项目」开始</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
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
          <div class="form-group">
            <label class="form-label">项目标识符</label>
            <input v-model="newProject.identifier" type="text" class="form-input"
              placeholder="如：codeseer-web（小写字母、数字、连字符）"
              :class="{ 'input-error': identifierError }"
              @input="validateIdentifier" />
            <div v-if="identifierError" class="field-error">{{ identifierError }}</div>
            <div v-else class="field-hint">用于文档路径和 AI 工具引用，创建后可修改</div>
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">项目描述</label>
            <textarea v-model="newProject.description" class="form-input" placeholder="简要描述项目目标..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn btn-primary" :disabled="!newProject.name.trim()" @click="createProject">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { projectsApi } from '@/api'

const projects = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const selected = ref<string[]>([])
const search = ref('')

const newProject = ref({ name: '', identifier: '', description: '' })
const identifierError = ref('')

const validateIdentifier = () => {
  const v = newProject.value.identifier
  if (!v) { identifierError.value = ''; return }
  if (!/^[a-z][a-z0-9-]{1,48}[a-z0-9]$/.test(v)) {
    identifierError.value = '只能包含小写字母、数字和连字符，长度 3-50，首尾为字母或数字'
  } else {
    identifierError.value = ''
  }
}

const filteredProjects = computed(() => {
  if (!search.value.trim()) return projects.value
  const q = search.value.trim().toLowerCase()
  return projects.value.filter((p: any) => p.name.toLowerCase().includes(q))
})

const isAllSelected = computed(() => {
  return filteredProjects.value.length > 0 && selected.value.length === filteredProjects.value.length
})

const toggleSelectAll = (e: Event) => {
  const checked = (e.target as HTMLInputElement).checked
  selected.value = checked ? filteredProjects.value.map((p: any) => p.id) : []
}

const statusText = (s: string) => ({ active: '进行中', archived: '已归档', completed: '已完成' }[s] || s)
const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

const fetchData = async () => {
  loading.value = true
  try { projects.value = (await projectsApi.list()).data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

const createProject = async () => {
  if (identifierError.value) return
  try {
    const payload: any = { name: newProject.value.name, description: newProject.value.description }
    if (newProject.value.identifier) payload.identifier = newProject.value.identifier
    await projectsApi.create(payload)
    showCreateModal.value = false
    newProject.value = { name: '', identifier: '', description: '' }
    identifierError.value = ''
    fetchData()
  } catch (e: any) {
    if (e?.response?.status === 409) identifierError.value = '该标识符已被其他项目使用'
    else console.error(e)
  }
}

const deleteProject = async (id: string) => {
  if (!confirm('确定删除此项目？')) return
  try { await projectsApi.delete(id); fetchData() } catch (e) { console.error(e) }
}

const batchDelete = async () => {
  if (!confirm(`确定删除 ${selected.value.length} 个项目？`)) return
  try { await Promise.all(selected.value.map((id: string) => projectsApi.delete(id))); selected.value = []; fetchData() }
  catch (e) { console.error(e) }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--color-text-secondary);
  font-size: 15px;
  pointer-events: none;
  z-index: 1;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--color-bg);
  border: 1px solid var(--color-sidebar-border);
  border-radius: 8px;
  margin-bottom: 12px;
}

.action-btns {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}

.row-selected {
  background: rgba(45, 91, 255, 0.04) !important;
}

.table th {
  background: var(--color-bg);
}

.identifier-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--color-bg);
  border: 1px solid var(--color-sidebar-border);
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  color: var(--color-text-secondary);
}

.input-error {
  border-color: #ef4444 !important;
}

.field-error {
  font-size: 12px;
  color: #ef4444;
  margin-top: 4px;
}

.field-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}
</style>
