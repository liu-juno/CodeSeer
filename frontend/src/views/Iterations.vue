<template>
  <div class="iterations-page">
    <!-- Page Header Toolbar -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">迭代管理</h1>
        <span class="text-muted text-medium" style="margin-left:12px;">{{ iterations.length }} 个迭代</span>
      </div>
      <div class="header-right">
        <div class="search-box">
          <span class="search-icon">⌕</span>
          <input v-model="search" type="text" class="form-input" placeholder="搜索迭代..." style="width:200px; padding-left:32px;" />
        </div>
        <select v-model="statusFilter" class="form-input" style="width:120px">
          <option value="">全部状态</option>
          <option value="planning">规划中</option>
          <option value="development">开发中</option>
          <option value="testing">测试中</option>
          <option value="released">已发布</option>
          <option value="archived">已归档</option>
        </select>
        <button class="btn btn-primary" @click="showCreateModal = true">
          <span>＋</span> 创建迭代
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
            <th>迭代名称</th>
            <th>所属项目</th>
            <th>状态</th>
            <th>计划发布日期</th>
            <th>创建时间</th>
            <th style="width:100px; text-align:right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="iter in filteredIterations" :key="iter.id" :class="{ 'row-selected': selected.includes(iter.id) }">
            <td>
              <input type="checkbox" :value="iter.id" v-model="selected" />
            </td>
            <td>
              <router-link :to="`/iteration/${iter.id}`" class="link" style="font-weight:600;">
                {{ iter.name }}
              </router-link>
            </td>
            <td class="text-muted text-medium">{{ getProjectName(iter.project_id) }}</td>
            <td>
              <span :class="['status-badge', iter.status]">{{ statusText(iter.status) }}</span>
            </td>
            <td class="text-muted text-medium">{{ iter.planned_release_date ? formatDate(iter.planned_release_date) : '—' }}</td>
            <td class="text-muted text-small">{{ formatDate(iter.created_at) }}</td>
            <td style="text-align:right;">
              <div class="action-btns">
                <router-link :to="`/iteration/${iter.id}`" class="btn btn-ghost btn-sm">查看</router-link>
                <button class="btn btn-ghost btn-sm" @click="deleteIteration(iter.id)" style="color:#ef4444;">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredIterations.length === 0">
            <td colspan="7">
              <div class="empty-state">
                <div class="empty-state-icon">↻</div>
                <div class="empty-state-text">暂无迭代，点击「创建迭代」开始</div>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { iterationsApi, projectsApi } from '@/api'

const route = useRoute()

const iterations = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const selected = ref<string[]>([])
const search = ref('')
const statusFilter = ref('')

const newIteration = ref({ name: '', description: '', project_id: '', planned_release_date: '' })

const filteredIterations = computed(() => {
  let list = iterations.value
  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase()
    list = list.filter((i: any) => i.name.toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    list = list.filter((i: any) => i.status === statusFilter.value)
  }
  return list
})

const isAllSelected = computed(() => {
  return filteredIterations.value.length > 0 && selected.value.length === filteredIterations.value.length
})

const toggleSelectAll = (e: Event) => {
  const checked = (e.target as HTMLInputElement).checked
  selected.value = checked ? filteredIterations.value.map((i: any) => i.id) : []
}

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
    await iterationsApi.create(newIteration.value)
    showCreateModal.value = false
    newIteration.value = { name: '', description: '', project_id: '', planned_release_date: '' }
    fetchData()
  } catch (e) {
    console.error(e)
  }
}

const deleteIteration = async (id: string) => {
  if (!confirm('确定删除此迭代？')) return
  try {
    await iterationsApi.delete(id)
    fetchData()
  } catch (e) {
    console.error(e)
  }
}

const batchDelete = async () => {
  if (!confirm(`确定删除 ${selected.value.length} 个迭代？`)) return
  try {
    await Promise.all(selected.value.map((id: string) => iterationsApi.delete(id)))
    selected.value = []
    fetchData()
  } catch (e) {
    console.error(e)
  }
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
</style>
